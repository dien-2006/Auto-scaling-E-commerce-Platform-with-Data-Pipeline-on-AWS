from decimal import Decimal
from uuid import UUID

from sqlalchemy import insert
from sqlalchemy.exc import DBAPIError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.errors import APIError
from app.db.locks import lock_category_tree
from app.models import Order, OrderItem, ShopOrder
from app.models.extensions import payments, shipments
from app.repositories.access import AccessRepository
from app.repositories.checkout import CheckoutRepository
from app.repositories.shopping import CouponRepository
from app.schemas.checkout import CheckoutRequest, OrderDetailData
from app.services.access import AccessPolicy
from app.services.checkout_options import CheckoutOptionsService
from app.services.shopping import CouponService

MAX_MONEY = Decimal("999999999999.99")


class CheckoutService:
    def __init__(self, session: Session, subject: int, settings: Settings | None = None):
        self.session = session
        self.subject = subject
        self.options = CheckoutOptionsService(settings or Settings())

    def checkout(self, payload: CheckoutRequest, key: UUID) -> tuple[OrderDetailData, bool]:
        # Own the transaction through COMMIT so deadlock/serialization retries
        # rerun authentication policy and all business checks, with the SAME key.
        for attempt in range(3):
            try:
                with self.session.begin():
                    access = AccessPolicy(AccessRepository(self.session, write=True), self.subject)
                    result = self._attempt(access, payload, key)
                return result
            except SQLAlchemyError as exc:
                orig = exc.orig if isinstance(exc, DBAPIError) else None
                code = getattr(orig, "sqlstate", None)
                constraint = getattr(getattr(orig, "diag", None), "constraint_name", None)
                retry = code in {"40001", "40P01"} or (
                    code == "23505" and constraint == "uq_orders_buyer_idempotency"
                )
                if retry and attempt < 2:
                    continue
                raise APIError(
                    503,
                    "DEPENDENCY_UNAVAILABLE",
                    "Chưa xác nhận được đơn hàng. Vui lòng thử lại cùng mã yêu cầu",
                ) from exc
        raise AssertionError("Unreachable")

    def _attempt(
        self, access: AccessPolicy, payload: CheckoutRequest, key: UUID
    ) -> tuple[OrderDetailData, bool]:
        repository = CheckoutRepository(self.session, access.buyer().user_id)
        previous = repository.existing(key)
        if previous is not None:
            return repository.detail(previous), True
        if self.options.settings.checkout_options_enabled and not payload.shipping_method:
            raise APIError(409, "QUOTE_REQUIRED", "Hãy chọn vận chuyển và xác nhận tổng tiền")
        cart = None
        if payload.purchase_mode == "BUY_NOW":
            items = payload.items
        else:
            cart = repository.cart()
            if cart is None:
                raise APIError(409, "CART_CHANGED", "Giỏ hàng đang trống hoặc đã thay đổi")
            items = repository.cart_items(cart.cart_id)
            if payload.purchase_mode == "SELECTED_CART":
                chosen = {item.product_id for item in payload.items}
                items = [item for item in items if item.product_id in chosen]
            if not items or {item.product_id: item.quantity for item in items} != {
                item.product_id: item.quantity for item in payload.items
            }:
                raise APIError(409, "CART_CHANGED", "Hãy tải lại và xác nhận toàn bộ giỏ hàng")
        wanted = {item.product_id: item for item in payload.items}
        address = repository.address(payload.address_id)
        if address is None:
            raise APIError(404, "NOT_FOUND", "Không tìm thấy địa chỉ giao hàng")
        lock_category_tree(self.session)
        shops, products, inventory = repository.lock_catalog([item.product_id for item in items])
        visible = repository.visible_categories()
        subtotals: dict[int, Decimal] = {}
        total = Decimal("0.00")
        for item in items:
            product = products[item.product_id]
            shop = shops[product.shop_id]
            if shop.owner_user_id == access.principal.user_id:
                raise APIError(403, "FORBIDDEN", "Không thể mua sản phẩm của shop mình")
            if (
                shop.shop_status != "APPROVED"
                or not product.is_active
                or product.category_id not in visible
            ):
                raise APIError(409, "CART_CHANGED", "Có sản phẩm hoặc gian hàng hiện không còn bán")
            if product.price != wanted[item.product_id].expected_unit_price:
                raise APIError(
                    409, "PRICE_CHANGED", "Giá sản phẩm đã thay đổi. Vui lòng xác nhận lại"
                )
            stock = inventory.get(item.product_id)
            if stock is None or stock.quantity < item.quantity:
                raise APIError(409, "OUT_OF_STOCK", "Sản phẩm không đủ tồn kho")
            amount = product.price * item.quantity
            total += amount
            subtotals[shop.shop_id] = subtotals.get(shop.shop_id, Decimal("0.00")) + amount
        if total > MAX_MONEY:
            raise APIError(409, "CART_CHANGED", "Tổng tiền vượt giới hạn đơn hàng")
        coupon_repository = CouponRepository(self.session)
        coupon_id, discount = None, Decimal("0.00")
        applied = []
        shipping_costs = []
        shipping_fee = shipping_discount = Decimal("0.00")
        self.options.payment(payload.payment_method)
        if payload.shipping_method:
            _, shipping_fee = self.options.shipping(payload.shipping_method, subtotals)
            applied, discount, shipping_discount = CouponService(coupon_repository).stack(
                payload, subtotals, access.principal.user_id, shipping_fee, lock=True
            )
            shipping_costs, shipping_fee = self.options.shipping(
                payload.shipping_method, subtotals, shipping_discount
            )
            if (
                payload.expected_shipping_fee is None
                or payload.expected_coupon_discount is None
                or payload.expected_shipping_discount is None
            ):
                raise APIError(409, "QUOTE_REQUIRED", "Hãy xác nhận lại tổng tiền trước khi đặt")
        if (
            payload.expected_shipping_fee is not None
            and payload.expected_shipping_fee != shipping_fee
        ):
            raise APIError(409, "SHIPPING_CHANGED", "Cước vận chuyển đã thay đổi")
        if (
            payload.expected_shipping_discount is not None
            and payload.expected_shipping_discount != shipping_discount
        ):
            raise APIError(409, "COUPON_CHANGED", "Mã giảm phí vận chuyển đã thay đổi")
        if payload.coupon_code:
            legacy_coupon = coupon_repository.find(payload.coupon_code)
            if legacy_coupon and legacy_coupon.get("coupon_type", "GOODS") != "GOODS":
                raise APIError(409, "COUPON_SCOPE", "Hãy nhập mã vận chuyển vào ô riêng")
            coupon_id, discount = CouponService(coupon_repository).calculate(
                payload.coupon_code, subtotals, access.principal.user_id, lock=True
            )
        if (
            payload.expected_coupon_discount is not None
            and payload.expected_coupon_discount != discount
        ):
            raise APIError(409, "COUPON_CHANGED", "Mức giảm đã thay đổi. Hãy áp dụng lại mã")
        order = Order(
            buyer_user_id=access.principal.user_id,
            idempotency_key=key,
            recipient_name=address.recipient_name,
            phone=address.phone,
            shipping_address=", ".join(
                part
                for part in [address.address_line, address.ward, address.district, address.city]
                if part
            ),
            total_amount=total - discount + shipping_fee,
            discount_amount=discount,
            shipping_fee=shipping_fee,
            **(
                {"shipping_discount_amount": shipping_discount}
                if hasattr(Order, "shipping_discount_amount")
                else {}
            ),
            payment_method=payload.payment_method,
        )
        self.session.add(order)
        if order.total_amount > MAX_MONEY:
            raise APIError(409, "CART_CHANGED", "Tổng thanh toán vượt giới hạn")
        self.session.flush()
        if coupon_id is not None:
            coupon_repository.consume(coupon_id, access.principal.user_id, order.order_id, discount)
        for used in applied:
            coupon_repository.consume(used[0], access.principal.user_id, order.order_id, used[3])
        child_orders = {}
        for shop_id, subtotal in sorted(subtotals.items()):
            child = ShopOrder(
                order_id=order.order_id, shop_id=shop_id, subtotal=subtotal, order_status="PENDING"
            )
            self.session.add(child)
            child_orders[shop_id] = child
        self.session.flush()
        for shipping in shipping_costs:
            self.session.execute(
                insert(shipments).values(
                    shop_order_id=child_orders[int(shipping.shop_id)].shop_order_id,
                    shipping_method="INSTANT"
                    if shipping.method == "COCOEXPRESS"
                    else shipping.method,
                    carrier="COCO Express" if shipping.method == "COCOEXPRESS" else "COCO",
                    shipping_fee=shipping.fee,
                )
            )
        if payload.shipping_method or payload.payment_method != "COD":
            self.session.execute(
                insert(payments).values(
                    order_id=order.order_id,
                    payment_method=payload.payment_method,
                    amount=order.total_amount,
                    payment_status="PENDING",
                    transaction_code=f"COCO{order.order_id}",
                )
            )
        for item in items:
            product = products[item.product_id]
            self.session.add(
                OrderItem(
                    shop_order_id=child_orders[product.shop_id].shop_order_id,
                    shop_id=product.shop_id,
                    product_id=product.product_id,
                    product_name=product.product_name,
                    unit_price=product.price,
                    quantity=item.quantity,
                )
            )
            repository.decrease_stock(item.product_id, item.quantity)
        self.session.flush()
        if cart is not None:
            repository.clear_cart(
                cart.cart_id,
                [item.product_id for item in items]
                if payload.purchase_mode == "SELECTED_CART"
                else None,
            )
        return repository.detail(order), False
