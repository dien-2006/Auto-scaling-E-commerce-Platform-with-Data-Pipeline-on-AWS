from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.core.config import Settings
from app.core.errors import APIError
from app.core.security import DUMMY_HASH, PASSWORD_HASHER, verify_password
from app.models import User
from app.repositories.access import AccessRepository
from app.repositories.users import UserRepository
from app.schemas.auth import LoginRequest, OwnedShop, RegisterRequest, UserPrivate
from app.services.access import AccessPolicy


class AuthService:
    def __init__(self, repository: UserRepository, settings: Settings | None = None) -> None:
        self.repository = repository
        self.settings = settings or Settings()
        self.login_hash: str | None = None

    def profile(self, user: User) -> UserPrivate:
        shop = self.repository.owned_shop(user.user_id)
        return UserPrivate(
            user_id=str(user.user_id),
            email=user.email,
            full_name=user.full_name,
            phone=user.phone,
            user_role=user.user_role,
            user_status=user.user_status,
            owned_shop=OwnedShop(shop_id=str(shop.shop_id), shop_status=shop.shop_status)
            if shop
            else None,
        )

    def register(self, data: RegisterRequest) -> UserPrivate:
        if self.settings.otp_enabled:
            raise APIError(403, "OTP_REQUIRED", "Vui lòng xác minh mã OTP để đăng ký")
        encoded = PASSWORD_HASHER.hash(data.password.get_secret_value())
        try:
            with self.repository.session.begin():
                if self.repository.by_email(str(data.email)):
                    raise APIError(409, "EMAIL_EXISTS", "Email đã được sử dụng")
                user = self.repository.add(
                    email=str(data.email),
                    password_hash=encoded,
                    full_name=data.full_name,
                    phone=data.phone,
                )
                result = self.profile(user)
            return result
        except IntegrityError as exc:
            if (
                getattr(exc.orig, "sqlstate", None) == "23505"
                and getattr(getattr(exc.orig, "diag", None), "constraint_name", None)
                == "uq_users_email_lower"
            ):
                raise APIError(409, "EMAIL_EXISTS", "Email đã được sử dụng") from exc
            raise APIError(503, "DEPENDENCY_UNAVAILABLE", "Dịch vụ chưa sẵn sàng") from exc
        except SQLAlchemyError as exc:
            raise APIError(503, "DEPENDENCY_UNAVAILABLE", "Dịch vụ chưa sẵn sàng") from exc

    def login(self, data: LoginRequest) -> UserPrivate:
        try:
            with self.repository.session.begin():
                user = self.repository.by_email(str(data.email))
                valid = verify_password(
                    user.password_hash if user else DUMMY_HASH, data.password.get_secret_value()
                )
                if not user or not valid:
                    raise APIError(401, "INVALID_CREDENTIALS", "Email hoặc mật khẩu không đúng")
                self.active(user)
                if PASSWORD_HASHER.check_needs_rehash(user.password_hash):
                    user.password_hash = PASSWORD_HASHER.hash(data.password.get_secret_value())
                self.login_hash = user.password_hash
                result = self.profile(user)
            return result
        except SQLAlchemyError as exc:
            raise APIError(503, "DEPENDENCY_UNAVAILABLE", "Dịch vụ chưa sẵn sàng") from exc

    def me(self, user_id: int) -> UserPrivate:
        try:
            with self.repository.session.begin():
                return AccessPolicy(AccessRepository(self.repository.session), user_id).profile()
        except SQLAlchemyError as exc:
            raise APIError(503, "DEPENDENCY_UNAVAILABLE", "Dịch vụ chưa sẵn sàng") from exc

    @staticmethod
    def active(user: User) -> None:
        if user.user_status != "ACTIVE":
            raise APIError(403, "USER_LOCKED", "Tài khoản đã bị khóa")
