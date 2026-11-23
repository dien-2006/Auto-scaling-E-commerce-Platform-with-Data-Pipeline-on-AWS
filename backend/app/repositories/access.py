"""Ownership predicates stay in SQL; no commits and no unrestricted resource lookups."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Address, Cart, Order, Product, Shop, ShopOrder, User


class AccessRepository:
    def __init__(self, session: Session, *, write: bool = False) -> None:
        self.session = session
        self.write = write

    def principal(self, user_id: int):
        query = select(
            User.user_id, User.user_role, User.user_status, User.email, User.full_name, User.phone
        ).where(User.user_id == user_id)
        if self.write:
            query = query.with_for_update()
        return self.session.execute(query).mappings().one_or_none()

    def shop(self, user_id: int):
        query = select(Shop.shop_id, Shop.shop_status).where(Shop.owner_user_id == user_id)
        if self.write:
            query = query.with_for_update()
        return self.session.execute(query).mappings().one_or_none()

    def address(self, resource_id: int, user_id: int) -> int | None:
        return self.session.scalar(
            select(Address.address_id).where(
                Address.address_id == resource_id, Address.user_id == user_id
            )
        )

    def cart(self, resource_id: int, user_id: int) -> int | None:
        return self.session.scalar(
            select(Cart.cart_id).where(Cart.cart_id == resource_id, Cart.user_id == user_id)
        )

    def order(self, resource_id: int, user_id: int) -> int | None:
        return self.session.scalar(
            select(Order.order_id).where(
                Order.order_id == resource_id, Order.buyer_user_id == user_id
            )
        )

    def buyer_shop_order(self, resource_id: int, user_id: int) -> int | None:
        return self.session.scalar(
            select(ShopOrder.shop_order_id)
            .join(Order, Order.order_id == ShopOrder.order_id)
            .where(ShopOrder.shop_order_id == resource_id, Order.buyer_user_id == user_id)
        )

    def product(self, resource_id: int, shop_id: int) -> int | None:
        return self.session.scalar(
            select(Product.product_id).where(
                Product.product_id == resource_id, Product.shop_id == shop_id
            )
        )

    def seller_shop_order(self, resource_id: int, shop_id: int) -> int | None:
        return self.session.scalar(
            select(ShopOrder.shop_order_id).where(
                ShopOrder.shop_order_id == resource_id, ShopOrder.shop_id == shop_id
            )
        )
