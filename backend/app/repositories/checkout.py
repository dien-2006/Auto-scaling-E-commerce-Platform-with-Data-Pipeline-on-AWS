from uuid import UUID

from sqlalchemy import delete, select, update
from sqlalchemy.orm import Session

from app.core.errors import APIError
from app.models import (
    Address,
    Cart,
    CartItem,
    Inventory,
    Order,
    Product,
    Shop,
)
from app.repositories.orders import OrderRepository
from app.repositories.products import public_categories


class CheckoutRepository(OrderRepository):
    def __init__(self, session: Session, buyer_id: int):
        self.session = session
        self.buyer_id = buyer_id

    def existing(self, key: UUID) -> Order | None:
        return self.session.scalar(
            select(Order).where(Order.buyer_user_id == self.buyer_id, Order.idempotency_key == key)
        )

    def cart(self) -> Cart | None:
        return self.session.scalar(
            select(Cart).where(Cart.user_id == self.buyer_id).with_for_update()
        )

    def cart_items(self, cart_id: int) -> list[CartItem]:
        return list(
            self.session.scalars(
                select(CartItem).where(CartItem.cart_id == cart_id).order_by(CartItem.product_id)
            )
        )

    def address(self, address_id: int) -> Address | None:
        return self.session.scalar(
            select(Address).where(
                Address.address_id == address_id, Address.user_id == self.buyer_id
            )
        )

    def lock_catalog(
        self, product_ids: list[int]
    ) -> tuple[dict[int, Shop], dict[int, Product], dict[int, Inventory]]:
        # Shop association is immutable in app APIs. Recheck after product locks
        # to reject unexpected reassignment without acquiring locks out of order.
        shop_ids = set(
            self.session.scalars(select(Product.shop_id).where(Product.product_id.in_(product_ids)))
        )
        shops = {
            shop.shop_id: shop
            for shop in self.session.scalars(
                select(Shop)
                .where(Shop.shop_id.in_(shop_ids))
                .order_by(Shop.shop_id)
                .with_for_update()
            )
        }
        products = {
            product.product_id: product
            for product in self.session.scalars(
                select(Product)
                .where(Product.product_id.in_(product_ids))
                .order_by(Product.product_id)
                .with_for_update()
            )
        }
        if len(products) != len(product_ids) or any(
            p.shop_id not in shops for p in products.values()
        ):
            raise APIError(409, "CART_CHANGED", "Sản phẩm trong giỏ đã thay đổi")
        stock = {
            row.product_id: row
            for row in self.session.scalars(
                select(Inventory)
                .where(Inventory.product_id.in_(product_ids))
                .order_by(Inventory.product_id)
                .with_for_update()
            )
        }
        return shops, products, stock

    def visible_categories(self) -> set[int]:
        tree = public_categories()
        return set(self.session.scalars(select(tree.c.category_id)))

    def decrease_stock(self, product_id: int, quantity: int) -> None:
        result = self.session.execute(
            update(Inventory)
            .where(Inventory.product_id == product_id, Inventory.quantity >= quantity)
            .values(quantity=Inventory.quantity - quantity)
            .returning(Inventory.product_id)
            .execution_options(synchronize_session=False)
        )
        if result.scalar_one_or_none() is None:
            raise APIError(409, "OUT_OF_STOCK", "Sản phẩm không đủ tồn kho")

    def clear_cart(self, cart_id: int, product_ids: list[int] | None = None) -> None:
        statement = delete(CartItem).where(CartItem.cart_id == cart_id)
        if product_ids is not None:
            statement = statement.where(CartItem.product_id.in_(product_ids))
        self.session.execute(statement)
