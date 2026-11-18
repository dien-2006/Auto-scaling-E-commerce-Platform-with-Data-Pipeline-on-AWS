from app.core.errors import APIError
from app.repositories.seller_orders import SellerOrderRepository
from app.repositories.shopping import CouponRepository


class SellerOrderService:
    def __init__(self, access, *, buyer=False):
        self.access = access
        self.repository = SellerOrderRepository(access.repository.session)
        self.shop_id = None
        self.buyer = buyer
        if not buyer:
            shop = access.owned_shop()
            if shop.shop_status not in {"APPROVED", "LOCKED"}:
                raise APIError(403, "SHOP_NOT_APPROVED", "Gian hàng chưa được phép xử lý đơn")
            self.shop_id = int(shop.shop_id)

    def owned(self, sid, order_id=None):
        row = self.repository.owned(
            sid,
            shop_id=self.shop_id,
            buyer_id=self.access.buyer().user_id if self.buyer else None,
            order_id=order_id,
        )
        if row is None:
            raise APIError(404, "NOT_FOUND", "Không tìm thấy đơn shop")
        return row

    def list(self, query):
        return self.repository.list(self.shop_id, query)

    def detail(self, sid):
        return self.repository.detail(self.owned(sid))

    def change(self, sid, target, expected=None, order_id=None):
        row, lines, stock = self.repository.lock_resources(self.owned(sid, order_id))
        # Same target is a no-op, including duplicate cancellation after a lost response.
        if row.order_status == target:
            return self.repository.detail(row)
        if target != "CANCELLED" and not self.repository.payment_ready(row.order_id):
            raise APIError(409, "PAYMENT_PENDING", "Đơn trả trước chưa được xác nhận thanh toán")
        allowed = (
            {"PENDING": {"CANCELLED"}}
            if self.buyer
            else {
                "PENDING": {"CONFIRMED", "CANCELLED"},
                "CONFIRMED": {"SHIPPING", "CANCELLED"},
                "SHIPPING": {"COMPLETED"},
            }
        )
        if (expected is not None and expected != row.order_status) or target not in allowed.get(
            row.order_status, set()
        ):
            raise APIError(
                409, "INVALID_TRANSITION", "Trạng thái đơn đã thay đổi hoặc không hợp lệ"
            )
        if target == "CANCELLED":
            for line in lines:
                inventory = stock.get(line.product_id)
                if inventory is None or inventory.quantity > 2147483647 - line.quantity:
                    raise APIError(
                        409, "RESTOCK_CONFLICT", "Chưa thể hoàn tồn, hãy liên hệ quản trị viên"
                    )
        if not self.repository.transition(row, target):
            raise APIError(409, "INVALID_TRANSITION", "Trạng thái đơn đã thay đổi")
        if target == "CANCELLED":
            for line in lines:
                if not self.repository.restore(line.product_id, line.quantity):
                    raise APIError(409, "RESTOCK_CONFLICT", "Chưa thể hoàn tồn")
            CouponRepository(self.repository.session).restore_cancelled(row.order_id)
            self.repository.stop_cancelled_payment(row.order_id)
        return self.repository.detail(row)
