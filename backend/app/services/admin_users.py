from app.core.errors import APIError
from app.repositories.admin_users import AdminUserRepository


class AdminUserService:
    def __init__(self, access):
        access.admin()
        self.repository = AdminUserRepository(access.repository.session)

    def list(self, query):
        return self.repository.list(query)

    def change(self, user_id, status):
        row = self.repository.get(user_id, write=True)
        if row is None:
            raise APIError(404, "NOT_FOUND", "Không tìm thấy người dùng")
        if row["user_role"] == "ADMIN":
            raise APIError(403, "ADMIN_PROTECTED", "Tài khoản quản trị viên chỉ được xem")
        if row["user_status"] == status:
            return self.repository.project(row)
        return self.repository.status(user_id, status)
