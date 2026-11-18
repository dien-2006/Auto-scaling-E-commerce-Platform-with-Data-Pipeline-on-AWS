from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Cart, CartItem, Inventory, Product, Shop
from app.repositories.products import primary_image_key, public_categories


class CartRepository:
    def __init__(self, session: Session, user_id: int):
        self.session = session
        self.user_id = user_id

    @staticmethod
    def products():
        visible = public_categories()
        return (
            select(
                Product.product_id,
                Product.product_name,
                Product.price,
                primary_image_key().label("primary_image_key"),
                Product.is_active,
                Shop.shop_id,
                Shop.shop_name,
                Shop.shop_slug,
                Shop.shop_status,
                Shop.owner_user_id,
                Inventory.quantity.label("available_quantity"),
                visible.c.category_id.label("visible_category_id"),
            )
            .join(Shop, Shop.shop_id == Product.shop_id)
            .outerjoin(Inventory, Inventory.product_id == Product.product_id)
            .outerjoin(visible, visible.c.category_id == Product.category_id)
        )

    def product(self, product_id: int):
        return (
            self.session.execute(self.products().where(Product.product_id == product_id))
            .mappings()
            .one_or_none()
        )

    def lines(self):
        # Include unavailable products so the buyer can remove them. No private
        # user fields are exposed; storage keys stay server-side for URL signing.
        statement = (
            self.products()
            .add_columns(CartItem.cart_item_id, CartItem.quantity)
            .join(CartItem, CartItem.product_id == Product.product_id)
            .join(Cart, Cart.cart_id == CartItem.cart_id)
            .where(Cart.user_id == self.user_id)
            .order_by(Shop.shop_id, CartItem.cart_item_id)
        )
        return self.session.execute(statement).mappings().all()

    def lock_cart(self, *, create: bool = False) -> Cart | None:
        cart = self.session.scalar(
            select(Cart).where(Cart.user_id == self.user_id).with_for_update()
        )
        if cart is None and create:
            # WriteAccess already holds the unique owner user row lock.
            cart = Cart(user_id=self.user_id)
            self.session.add(cart)
            self.session.flush()
        return cart

    def item(
        self, cart_id: int, *, item_id: int | None = None, product_id: int | None = None
    ) -> CartItem | None:
        query = select(CartItem).where(CartItem.cart_id == cart_id)
        query = (
            query.where(CartItem.cart_item_id == item_id)
            if item_id is not None
            else query.where(CartItem.product_id == product_id)
        )
        return self.session.scalar(query.with_for_update())
