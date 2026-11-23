from collections.abc import Sequence

from sqlalchemy import func, literal_column, select, text
from sqlalchemy.engine import RowMapping
from sqlalchemy.orm import Session

from app.models import Category, Inventory, OrderItem, Product, ProductImage, Shop, ShopOrder
from app.schemas.products import ProductQuery


def primary_image_key():
    return (
        select(ProductImage.image_key)
        .where(ProductImage.product_id == Product.product_id)
        .order_by(
            ProductImage.is_primary.desc(), ProductImage.sort_order, ProductImage.product_image_id
        )
        .limit(1)
        .correlate(Product)
        .scalar_subquery()
    )


def public_categories():
    # Starting at active roots excludes inactive ancestors, orphans and disconnected cycles.
    tree = (
        select(Category.category_id, Category.parent_category_id)
        .where(Category.is_active.is_(True), Category.parent_category_id.is_(None))
        .cte("public_categories", recursive=True)
    )
    return tree.union(
        select(Category.category_id, Category.parent_category_id)
        .join(tree, Category.parent_category_id == tree.c.category_id)
        .where(Category.is_active.is_(True))
    )


class ProductRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def public_statement(self, query: ProductQuery):
        visible = public_categories()
        statement = (
            select(
                Product.product_id,
                Product.product_name,
                Product.price,
                Product.category_id,
                Product.description,
                Product.sku,
                primary_image_key().label("primary_image_key"),
                Shop.shop_id,
                Shop.shop_name,
                Shop.shop_slug,
                func.coalesce(Inventory.quantity, 0).label("available_quantity"),
            )
            .join(Shop, Product.shop_id == Shop.shop_id)
            .join(visible, Product.category_id == visible.c.category_id)
            .outerjoin(Inventory, Product.product_id == Inventory.product_id)
            .where(Product.is_active.is_(True), Shop.shop_status == "APPROVED")
        )
        if query.q.strip():
            # autoescape treats %, _ and the escape character as literal search text.
            statement = statement.where(
                Product.product_name.icontains(query.q.strip(), autoescape=True)
            )
        if query.shop_id is not None:
            statement = statement.where(Product.shop_id == query.shop_id)
        if query.category_id is not None:
            branch = (
                select(visible.c.category_id)
                .where(visible.c.category_id == query.category_id)
                .cte("category_branch", recursive=True)
            )
            branch = branch.union(
                select(visible.c.category_id).join(
                    branch, visible.c.parent_category_id == branch.c.category_id
                )
            )
            statement = statement.where(Product.category_id.in_(select(branch.c.category_id)))
        return statement

    def list(self, query: ProductQuery) -> tuple[Sequence[RowMapping], int]:
        statement = self.public_statement(query)
        total = self.session.scalar(select(func.count()).select_from(statement.subquery()))
        # Never accept SQL fragments from query parameters. ID is a stable tie-breaker.
        ordering = {
            "newest": (Product.created_at.desc(), Product.product_id.desc()),
            "price_asc": (Product.price.asc(), Product.product_id.desc()),
            "price_desc": (Product.price.desc(), Product.product_id.desc()),
        }
        rows = (
            self.session.execute(
                statement.order_by(*ordering[query.sort])
                .offset((query.page - 1) * query.page_size)
                .limit(query.page_size)
            )
            .mappings()
            .all()
        )
        return rows, int(total or 0)

    def detail(self, product_id: int) -> RowMapping | None:
        return (
            self.session.execute(
                self.public_statement(ProductQuery()).where(Product.product_id == product_id)
            )
            .mappings()
            .one_or_none()
        )

    def images(self, product_id: int) -> Sequence[RowMapping]:
        # Storage keys stay server-side; response schemas only expose delivery URLs.
        return (
            self.session.execute(
                select(
                    ProductImage.product_image_id,
                    ProductImage.is_primary,
                    ProductImage.sort_order,
                    ProductImage.image_key,
                )
                .where(ProductImage.product_id == product_id)
                .order_by(
                    ProductImage.is_primary.desc(),
                    ProductImage.sort_order.asc(),
                    ProductImage.product_image_id.asc(),
                )
            )
            .mappings()
            .all()
        )

    def deals(self):
        visible = self.public_statement(ProductQuery()).subquery()
        statement = (
            select(
                visible,
                literal_column("d.original_price").label("original_price"),
                literal_column("d.sale_price").label("sale_price"),
                literal_column("d.discount_percent").label("discount_percent"),
                literal_column("to_jsonb(d)->>'coupon_code'").label("coupon_code"),
                literal_column("to_jsonb(d)->>'ends_at'").label("ends_at"),
            )
            .select_from(
                visible.join(
                    text("marketplace.v_deal_today AS d"),
                    visible.c.product_id == text("d.product_id"),
                )
            )
            .where(
                visible.c.available_quantity > 0,
                literal_column("d.discount_percent") > 0,
                literal_column("d.discount_percent") < 30,
                literal_column("d.sale_price") < literal_column("d.original_price"),
            )
            .order_by(visible.c.product_id.desc())
            .limit(100)
        )
        return self.session.execute(statement).mappings().all()

    def bestsellers(self):
        sold = (
            select(OrderItem.product_id, func.sum(OrderItem.quantity).label("sold"))
            .join(ShopOrder, OrderItem.shop_order_id == ShopOrder.shop_order_id)
            .where(ShopOrder.order_status == "COMPLETED")
            .group_by(OrderItem.product_id)
            .subquery()
        )
        visible = self.public_statement(ProductQuery()).subquery()
        statement = (
            select(visible)
            .join(sold, visible.c.product_id == sold.c.product_id)
            .order_by(sold.c.sold.desc(), visible.c.product_id.desc())
            .limit(12)
        )
        rows = self.session.execute(statement).mappings().all()
        if rows:
            return rows, True
        rows, _ = self.list(ProductQuery(page_size=12))
        return rows, False
