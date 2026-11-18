from datetime import UTC

from sqlalchemy import func, literal, select
from sqlalchemy.orm import Session

from app.models import Order, OrderItem, Shop, ShopOrder
from app.models.extensions import coupon_usages, coupons, payments, shipments
from app.schemas.checkout import OrderDetailData, OrderLineData, ShopOrderData
from app.schemas.checkout_options import AppliedCoupon
from app.schemas.orders import OrderList, OrderQuery, OrderSummary, ShopOrderSummary


class OrderRepository:
    def __init__(self, session: Session, buyer_id: int):
        self.session = session
        self.buyer_id = buyer_id

    def owned(self, order_id: int) -> Order | None:
        return self.session.scalar(
            select(Order).where(Order.order_id == order_id, Order.buyer_user_id == self.buyer_id)
        )

    def list(self, query: OrderQuery) -> OrderList:
        predicate = Order.buyer_user_id == self.buyer_id
        total = self.session.scalar(select(func.count()).select_from(Order).where(predicate)) or 0
        orders = list(
            self.session.scalars(
                select(Order)
                .where(predicate)
                .order_by(Order.created_at.desc(), Order.order_id.desc())
                .offset((query.page - 1) * query.page_size)
                .limit(query.page_size)
            )
        )
        grouped: dict[int, list[ShopOrderSummary]] = {}
        if orders:
            rows = self.session.execute(
                select(ShopOrder, Shop.shop_name)
                .join(Shop, Shop.shop_id == ShopOrder.shop_id)
                .where(ShopOrder.order_id.in_([order.order_id for order in orders]))
                .order_by(ShopOrder.shop_id)
            ).all()
            for shop, name in rows:
                grouped.setdefault(shop.order_id, []).append(
                    ShopOrderSummary(
                        shop_order_id=str(shop.shop_order_id),
                        shop_id=str(shop.shop_id),
                        shop_name=name,
                        order_status=shop.order_status,
                        subtotal=shop.subtotal,
                    )
                )
        return OrderList(
            items=[
                OrderSummary(
                    order_id=str(order.order_id),
                    total_amount=order.total_amount,
                    discount_amount=order.discount_amount,
                    shipping_fee=order.shipping_fee,
                    payment_method=order.payment_method,
                    created_at=order.created_at.astimezone(UTC),
                    shop_orders=grouped.get(order.order_id, []),
                )
                for order in orders
            ],
            page=query.page,
            page_size=query.page_size,
            total=total,
        )

    def detail(self, order: Order) -> OrderDetailData:
        # Order was selected/created for this buyer. Product and address snapshots
        # come only from order tables, never from mutable catalog/address rows.
        shop_rows = self.session.execute(
            select(ShopOrder, Shop.shop_name)
            .join(Shop, Shop.shop_id == ShopOrder.shop_id)
            .where(ShopOrder.order_id == order.order_id)
            .order_by(ShopOrder.shop_id)
        ).all()
        lines = list(
            self.session.scalars(
                select(OrderItem)
                .join(ShopOrder, ShopOrder.shop_order_id == OrderItem.shop_order_id)
                .where(ShopOrder.order_id == order.order_id)
                .order_by(OrderItem.order_item_id)
            )
        )
        grouped: dict[int, list[OrderLineData]] = {}
        delivery = {
            r["shop_order_id"]: r
            for r in self.session.execute(
                select(shipments)
                .join(ShopOrder, ShopOrder.shop_order_id == shipments.c.shop_order_id)
                .where(ShopOrder.order_id == order.order_id)
            ).mappings()
        }
        applied = (
            self.session.execute(
                select(
                    coupon_usages.c.discount_amount,
                    coupons.c.code,
                    coupons.c.shop_id,
                    getattr(coupons.c, "coupon_type", literal("GOODS")).label("coupon_type"),
                )
                .join(coupons, coupons.c.coupon_id == coupon_usages.c.coupon_id)
                .where(coupon_usages.c.order_id == order.order_id)
                .order_by(coupon_usages.c.usage_id)
            )
            .mappings()
            .all()
        )
        for row in lines:
            grouped.setdefault(row.shop_order_id, []).append(
                OrderLineData(
                    order_item_id=str(row.order_item_id),
                    product_id=str(row.product_id),
                    product_name=row.product_name,
                    unit_price=row.unit_price,
                    quantity=row.quantity,
                    line_total=row.unit_price * row.quantity,
                )
            )
        return OrderDetailData(
            order_id=str(order.order_id),
            total_amount=order.total_amount,
            discount_amount=order.discount_amount,
            shipping_fee=order.shipping_fee,
            shipping_discount_amount=getattr(order, "shipping_discount_amount", 0),
            applied_coupons=[
                AppliedCoupon(
                    code=r["code"],
                    shop_id=str(r["shop_id"]) if r["shop_id"] else None,
                    coupon_type=r["coupon_type"],
                    discount_amount=r["discount_amount"],
                )
                for r in applied
            ],
            payment_status=self.session.scalar(
                select(payments.c.payment_status)
                .where(payments.c.order_id == order.order_id)
                .order_by(payments.c.payment_id.desc())
                .limit(1)
            ),
            payment_method=order.payment_method,
            created_at=order.created_at.astimezone(UTC),
            recipient_name=order.recipient_name,
            phone=order.phone,
            shipping_address=order.shipping_address,
            shop_orders=[
                ShopOrderData(
                    shop_order_id=str(shop_order.shop_order_id),
                    shop_id=str(shop_order.shop_id),
                    shop_name=name,
                    order_status=shop_order.order_status,
                    subtotal=shop_order.subtotal,
                    shipping_method=(
                        "COCOEXPRESS"
                        if delivery[shop_order.shop_order_id]["shipping_method"] == "INSTANT"
                        else delivery[shop_order.shop_order_id]["shipping_method"]
                    )
                    if shop_order.shop_order_id in delivery
                    else None,
                    shipping_fee=delivery[shop_order.shop_order_id]["shipping_fee"]
                    if shop_order.shop_order_id in delivery
                    else 0,
                    items=grouped.get(shop_order.shop_order_id, []),
                )
                for shop_order, name in shop_rows
            ],
        )
