from app.core.errors import APIError
from app.repositories.admin_shops import AdminShopRepository


class AdminShopService:
    def __init__(self, access):
        access.admin()
        self.repository = AdminShopRepository(access.repository.session)

    def list(self, query):
        return self.repository.list(query)

    def change(self, shop_id, expected, target):
        # WriteAccess already locks the active Admin user. Shop lock is shared with checkout.
        row = self.repository.get(shop_id, write=True)
        if row is None:
            raise APIError(404, "NOT_FOUND", "Không tìm thấy gian hàng")
        if row["shop_status"] == target:
            return self.repository.project(row)
        allowed = {"PENDING": {"APPROVED", "REJECTED"}, "APPROVED": {"LOCKED"}}
        if row["shop_status"] != expected or target not in allowed.get(expected, set()):
            raise APIError(
                409, "INVALID_TRANSITION", "Trạng thái gian hàng đã thay đổi hoặc không hợp lệ"
            )
        if not self.repository.transition(shop_id, expected, target):
            raise APIError(409, "INVALID_TRANSITION", "Trạng thái gian hàng đã thay đổi")
        return self.repository.project(self.repository.get(shop_id))
