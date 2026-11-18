from decimal import Decimal

from sqlalchemy import func, insert, select, update
from sqlalchemy.orm import Session

from app.models import Cart, CartItem, Order, OrderItem, Product, Shop, ShopOrder
from app.models.extensions import coupon_usages, coupons, product_reviews
from app.repositories.products import public_categories


class CouponRepository:
    def __init__(self, session: Session):
        self.session = session

    def find(self, code: str, *, lock: bool = False):
        query = select(coupons).where(coupons.c.code == code)
        if lock:
            query = query.with_for_update()
        return self.session.execute(query).mappings().one_or_none()

    def now(self):
        return self.session.scalar(select(func.clock_timestamp()))

    def selected(self, codes, *, lock=False):
        query = select(coupons).where(coupons.c.code.in_(codes)).order_by(coupons.c.coupon_id)
        if lock:
            query = query.with_for_update()
        return self.session.execute(query).mappings().all()

    def active_uses(self, coupon_id: int, buyer_id: int):
        outstanding = (
            select(ShopOrder.shop_order_id)
            .where(
                ShopOrder.order_id == coupon_usages.c.order_id,
                ShopOrder.order_status != "CANCELLED",
            )
            .exists()
        )
        return (
            self.session.scalar(
                select(func.count())
                .select_from(coupon_usages)
                .where(
                    coupon_usages.c.coupon_id == coupon_id,
                    coupon_usages.c.user_id == buyer_id,
                    outstanding,
                )
            )
            or 0
        )

    def restore_cancelled(self, order_id: int):
        usages = (
            self.session.execute(select(coupon_usages).where(coupon_usages.c.order_id == order_id))
            .mappings()
            .all()
        )
        if not usages:
            return
        self.session.execute(
            select(coupons.c.coupon_id)
            .where(coupons.c.coupon_id.in_([u["coupon_id"] for u in usages]))
            .order_by(coupons.c.coupon_id)
            .with_for_update()
        ).all()
        outstanding = self.session.scalar(
            select(func.count())
            .select_from(ShopOrder)
            .where(ShopOrder.order_id == order_id, ShopOrder.order_status != "CANCELLED")
        )
        if not outstanding:
            for usage in usages:
                self.session.execute(
                    update(coupons)
                    .where(coupons.c.coupon_id == usage["coupon_id"], coupons.c.used_count > 0)
                    .values(used_count=coupons.c.used_count - 1)
                )

    def cart(self, buyer_id: int):
        visible = public_categories()
        return (
            self.session.execute(
                select(
                    Product.product_id,
                    Product.shop_id,
                    Product.price,
                    CartItem.quantity,
                    Product.is_active,
                    Shop.shop_status,
                    Shop.owner_user_id,
                    Product.category_id.in_(select(visible.c.category_id)).label("visible"),
                )
                .select_from(CartItem)
                .join(Cart, Cart.cart_id == CartItem.cart_id)
                .join(Product, Product.product_id == CartItem.product_id)
                .join(Shop, Shop.shop_id == Product.shop_id)
                .where(Cart.user_id == buyer_id)
            )
            .mappings()
            .all()
        )

    def consume(self, coupon_id: int, buyer_id: int, order_id: int, discount: Decimal):
        self.session.execute(
            update(coupons)
            .where(coupons.c.coupon_id == coupon_id)
            .values(used_count=coupons.c.used_count + 1)
        )
        self.session.execute(
            insert(coupon_usages).values(
                coupon_id=coupon_id,
                user_id=buyer_id,
                order_id=order_id,
                discount_amount=discount,
            )
        )


class ReviewRepository:
    def __init__(self, session: Session):
        self.session = session

    def owned_line(self, item_id: int, buyer_id: int, *, lock: bool = False):
        query = (
            select(OrderItem.product_id, ShopOrder.order_status)
            .join(ShopOrder, ShopOrder.shop_order_id == OrderItem.shop_order_id)
            .join(Order, Order.order_id == ShopOrder.order_id)
            .where(OrderItem.order_item_id == item_id, Order.buyer_user_id == buyer_id)
        )
        if lock:
            query = query.with_for_update(of=ShopOrder)
        return self.session.execute(query).mappings().one_or_none()

    def existing(self, item_id: int):
        return (
            self.session.execute(
                select(product_reviews).where(product_reviews.c.order_item_id == item_id)
            )
            .mappings()
            .one_or_none()
        )

    def create(self, item_id: int, product_id: int, buyer_id: int, rating: int, comment):
        return (
            self.session.execute(
                insert(product_reviews)
                .values(
                    order_item_id=item_id,
                    product_id=product_id,
                    user_id=buyer_id,
                    rating=rating,
                    comment=comment,
                )
                .returning(product_reviews)
            )
            .mappings()
            .one()
        )

    def public(self, product_id: int, page: int, page_size: int):
        # Count only reviews tied to the same buyer/product and a completed purchase.
        source = (
            product_reviews.join(
                OrderItem, OrderItem.order_item_id == product_reviews.c.order_item_id
            )
            .join(ShopOrder, ShopOrder.shop_order_id == OrderItem.shop_order_id)
            .join(Order, Order.order_id == ShopOrder.order_id)
        )
        filters = [
            product_reviews.c.product_id == product_id,
            OrderItem.product_id == product_id,
            Order.buyer_user_id == product_reviews.c.user_id,
            ShopOrder.order_status == "COMPLETED",
        ]
        count, average = self.session.execute(
            select(func.count(), func.avg(product_reviews.c.rating))
            .select_from(source)
            .where(*filters)
        ).one()
        rows = (
            self.session.execute(
                select(product_reviews)
                .select_from(source)
                .where(*filters)
                .order_by(product_reviews.c.created_at.desc(), product_reviews.c.review_id.desc())
                .offset((page - 1) * page_size)
                .limit(page_size)
            )
            .mappings()
            .all()
        )
        return rows, count, average
