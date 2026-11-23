from sqlalchemy import func, or_, select, update

from app.models import Inventory, Product, Shop
from app.repositories.products import primary_image_key
from app.repositories.seller_products import SellerProductRepository


class AdminProductRepository:
    def __init__(self, session):
        self.session = session

    def statement(self):
        return (
            select(
                Product.product_id,
                Product.product_name,
                Product.price,
                Product.category_id,
                Product.description,
                Product.sku,
                primary_image_key().label("primary_image_key"),
                Product.is_active,
                Product.created_at,
                Product.updated_at,
                Shop.shop_id,
                Shop.shop_name,
                Shop.shop_slug,
                func.coalesce(Inventory.quantity, 0).label("available_quantity"),
            )
            .join(Shop, Shop.shop_id == Product.shop_id)
            .outerjoin(Inventory, Inventory.product_id == Product.product_id)
        )

    def list(self, query):
        statement = self.statement()
        if query.q.strip():
            statement = statement.where(
                or_(
                    Product.product_name.icontains(query.q.strip(), autoescape=True),
                    Product.sku.icontains(query.q.strip(), autoescape=True),
                )
            )
        if query.shop_id is not None:
            statement = statement.where(Product.shop_id == query.shop_id)
        if query.is_active is not None:
            statement = statement.where(Product.is_active == query.is_active)
        total = self.session.scalar(select(func.count()).select_from(statement.subquery()))
        rows = (
            self.session.execute(
                statement.order_by(Product.created_at.desc(), Product.product_id.desc())
                .offset((query.page - 1) * query.page_size)
                .limit(query.page_size)
            )
            .mappings()
            .all()
        )
        return rows, total or 0

    def detail(self, product_id):
        return (
            self.session.execute(self.statement().where(Product.product_id == product_id))
            .mappings()
            .one_or_none()
        )

    def images(self, ids):
        # Reuse the batch image query only; Admin authorization is enforced by the service.
        return SellerProductRepository(self.session, 0).images(ids)

    def lock(self, product_id):
        shop_id = self.session.scalar(
            select(Product.shop_id).where(Product.product_id == product_id)
        )
        if shop_id is None:
            return None
        self.session.execute(
            select(Shop.shop_id).where(Shop.shop_id == shop_id).with_for_update()
        ).all()
        return (
            self.session.execute(
                select(Product.product_id, Product.is_active)
                .where(Product.product_id == product_id, Product.shop_id == shop_id)
                .with_for_update()
            )
            .mappings()
            .one_or_none()
        )

    def hide(self, product_id):
        self.session.execute(
            update(Product)
            .where(Product.product_id == product_id, Product.is_active.is_(True))
            .values(is_active=False, updated_at=func.now())
            .execution_options(synchronize_session=False)
        )
