from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Inventory, Product, ProductImage, Shop
from app.repositories.products import primary_image_key, public_categories
from app.schemas.seller_products import SellerQuery


class SellerProductRepository:
    def __init__(self, session: Session, shop_id: int):
        self.session = session
        self.shop_id = shop_id

    def owned(self, product_id: int, *, write: bool = False):
        query = select(Product).where(
            Product.product_id == product_id, Product.shop_id == self.shop_id
        )
        if write:
            query = query.with_for_update()
        return self.session.scalar(query)

    def valid_category(self, category_id: int):
        tree = public_categories()
        return (
            self.session.scalar(select(tree.c.category_id).where(tree.c.category_id == category_id))
            is not None
        )

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
            .where(Product.shop_id == self.shop_id)
        )

    def detail(self, product_id: int):
        return (
            self.session.execute(self.statement().where(Product.product_id == product_id))
            .mappings()
            .one_or_none()
        )

    def list(self, query: SellerQuery):
        statement = self.statement()
        if query.q.strip():
            statement = statement.where(
                Product.product_name.icontains(query.q.strip(), autoescape=True)
            )
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
        return rows, int(total or 0)

    def images(self, ids: list[int]):
        return (
            self.session.execute(
                select(
                    ProductImage.product_id,
                    ProductImage.product_image_id,
                    ProductImage.image_key,
                    ProductImage.is_primary,
                    ProductImage.sort_order,
                )
                .where(ProductImage.product_id.in_(ids))
                .order_by(
                    ProductImage.is_primary.desc(),
                    ProductImage.sort_order,
                    ProductImage.product_image_id,
                )
            )
            .mappings()
            .all()
            if ids
            else []
        )
