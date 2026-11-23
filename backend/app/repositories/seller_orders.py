from datetime import UTC

from sqlalchemy import func, select, update

from app.models import Inventory, Order, OrderItem, Product, Shop, ShopOrder, User
from app.models.extensions import payments
from app.schemas.checkout import OrderLineData
from app.schemas.seller_orders import SellerOrderDetail, SellerOrderList, SellerOrderSummary


class SellerOrderRepository:
    def __init__(self, session):
        self.session = session

    def payment_ready(self, order_id):
        order = self.session.execute(
            select(Order.payment_method, Order.total_amount).where(Order.order_id == order_id)
        ).one()
        if order.payment_method == "COD":
            return True
        return (
            self.session.scalar(
                select(payments.c.payment_id)
                .where(
                    payments.c.order_id == order_id,
                    payments.c.payment_status == "SUCCESS",
                    payments.c.payment_method == order.payment_method,
                    payments.c.amount == order.total_amount,
                )
                .limit(1)
            )
            is not None
        )

    def stop_cancelled_payment(self, order_id):
        # Serialize final cancellations even when the order has no coupon.
        self.session.execute(
            select(payments.c.payment_id)
            .where(payments.c.order_id == order_id)
            .order_by(payments.c.payment_id)
            .with_for_update()
        ).all()
        outstanding = self.session.scalar(
            select(func.count())
            .select_from(ShopOrder)
            .where(ShopOrder.order_id == order_id, ShopOrder.order_status != "CANCELLED")
        )
        if not outstanding:
            self.session.execute(
                update(payments)
                .where(payments.c.order_id == order_id, payments.c.payment_status == "PENDING")
                .values(payment_status="FAILED")
            )

    def owned(self, sid, *, shop_id=None, buyer_id=None, order_id=None):
        query = select(ShopOrder).join(Order, Order.order_id == ShopOrder.order_id)
        query = query.where(ShopOrder.shop_order_id == sid)
        if shop_id is not None:
            query = query.where(ShopOrder.shop_id == shop_id)
        if buyer_id is not None:
            query = query.where(Order.buyer_user_id == buyer_id, Order.order_id == order_id)
        return self.session.scalar(query)

    @staticmethod
    def summary(row):
        return SellerOrderSummary(
            shop_order_id=str(row.shop_order_id),
            order_id=str(row.order_id),
            shop_id=str(row.shop_id),
            order_status=row.order_status,
            subtotal=row.subtotal,
            created_at=row.created_at.astimezone(UTC),
            updated_at=row.updated_at.astimezone(UTC),
        )

    def list(self, shop_id, query):
        predicates = [ShopOrder.shop_id == shop_id]
        if query.status:
            predicates.append(ShopOrder.order_status == query.status)
        total = self.session.scalar(select(func.count()).select_from(ShopOrder).where(*predicates))
        rows = self.session.scalars(
            select(ShopOrder)
            .where(*predicates)
            .order_by(ShopOrder.created_at.desc(), ShopOrder.shop_order_id.desc())
            .offset((query.page - 1) * query.page_size)
            .limit(query.page_size)
        )
        return SellerOrderList(
            items=[self.summary(r) for r in rows],
            page=query.page,
            page_size=query.page_size,
            total=total or 0,
        )

    def lines(self, row):
        return list(
            self.session.scalars(
                select(OrderItem)
                .where(OrderItem.shop_order_id == row.shop_order_id)
                .order_by(OrderItem.product_id)
            )
        )

    def detail(self, row):
        # Read only the seller contract, independent of un-applied checkout columns.
        order = self.session.execute(
            select(
                Order.recipient_name,
                Order.phone,
                Order.shipping_address,
                Order.payment_method,
                User.full_name.label("buyer_name"),
            )
            .join(User, User.user_id == Order.buyer_user_id)
            .where(Order.order_id == row.order_id)
        ).one()
        return SellerOrderDetail(
            **self.summary(row).model_dump(),
            buyer_name=order.buyer_name,
            recipient_name=order.recipient_name,
            phone=order.phone,
            shipping_address=order.shipping_address,
            payment_method=order.payment_method,
            items=[
                OrderLineData(
                    order_item_id=str(r.order_item_id),
                    product_id=str(r.product_id),
                    product_name=r.product_name,
                    unit_price=r.unit_price,
                    quantity=r.quantity,
                    line_total=r.unit_price * r.quantity,
                )
                for r in self.lines(row)
            ],
        )

    def lock_resources(self, row):
        # Ownership was checked before taking resource locks. Snapshot lines are immutable.
        self.session.execute(
            select(Shop.shop_id).where(Shop.shop_id == row.shop_id).with_for_update()
        ).all()
        lines = self.lines(row)
        ids = [line.product_id for line in lines]
        self.session.execute(
            select(Product.product_id)
            .where(Product.product_id.in_(ids))
            .order_by(Product.product_id)
            .with_for_update()
        ).all()
        stock = list(
            self.session.scalars(
                select(Inventory)
                .where(Inventory.product_id.in_(ids))
                .order_by(Inventory.product_id)
                .with_for_update()
                .execution_options(populate_existing=True)
            )
        )
        locked = self.session.scalar(
            select(ShopOrder)
            .where(ShopOrder.shop_order_id == row.shop_order_id)
            .with_for_update()
            .execution_options(populate_existing=True)
        )
        return locked, lines, {r.product_id: r for r in stock}

    def transition(self, row, target):
        result = self.session.execute(
            update(ShopOrder)
            .where(
                ShopOrder.shop_order_id == row.shop_order_id,
                ShopOrder.order_status == row.order_status,
            )
            .values(order_status=target, updated_at=func.now())
            .execution_options(synchronize_session=False)
        )
        self.session.refresh(row)
        return result.rowcount == 1

    def restore(self, product_id, quantity):
        return (
            self.session.execute(
                update(Inventory)
                .where(
                    Inventory.product_id == product_id, Inventory.quantity <= 2147483647 - quantity
                )
                .values(quantity=Inventory.quantity + quantity, updated_at=func.now())
                .execution_options(synchronize_session=False)
            ).rowcount
            == 1
        )
