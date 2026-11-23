"""Request-scoped policies. Caller keeps one transaction open through the operation."""

from dataclasses import dataclass

from app.core.errors import APIError
from app.repositories.access import AccessRepository
from app.schemas.auth import OwnedShop, UserPrivate


@dataclass(frozen=True)
class Principal:
    user_id: int
    user_role: str
    user_status: str
    email: str | None
    full_name: str
    phone: str | None


class AccessPolicy:
    def __init__(self, repository: AccessRepository, subject: int) -> None:
        self.repository = repository
        row = repository.principal(subject)
        if row is None:
            raise APIError(401, "INVALID_TOKEN", "Phiên đăng nhập không hợp lệ")
        self.principal = Principal(**row)
        if self.principal.user_status != "ACTIVE":
            raise APIError(403, "USER_LOCKED", "Tài khoản đã bị khóa")
        if self.principal.user_role not in {"USER", "ADMIN"}:
            raise APIError(403, "FORBIDDEN", "Bạn không có quyền truy cập")

    def admin(self) -> Principal:
        if self.principal.user_role != "ADMIN":
            raise APIError(403, "FORBIDDEN", "Bạn không có quyền truy cập")
        return self.principal

    def buyer(self) -> Principal:
        if self.principal.user_role != "USER":
            raise APIError(
                403,
                "COMMERCE_FORBIDDEN",
                "Tài khoản quản trị viên không được mua hàng hoặc tạo gian hàng",
            )
        return self.principal

    def owned_shop(self) -> OwnedShop:
        row = self.repository.shop(self.principal.user_id)
        if row is None:
            raise APIError(403, "FORBIDDEN", "Tài khoản chưa sở hữu gian hàng")
        return OwnedShop(shop_id=str(row["shop_id"]), shop_status=row["shop_status"])

    def selling_shop(self) -> OwnedShop:
        shop = self.owned_shop()
        self._approved(shop)
        return shop

    def shop(self, shop_id: int) -> OwnedShop:
        shop = self.owned_shop()
        self._owned(shop_id, int(shop.shop_id) if self._valid_id(shop_id) else None)
        return shop

    def address(self, address_id: int) -> int:
        return self._owned(address_id, self.repository.address(address_id, self.principal.user_id))

    def cart(self, cart_id: int) -> int:
        return self._owned(cart_id, self.repository.cart(cart_id, self.principal.user_id))

    def order(self, order_id: int) -> int:
        return self._owned(order_id, self.repository.order(order_id, self.principal.user_id))

    def buyer_shop_order(self, shop_order_id: int) -> int:
        return self._owned(
            shop_order_id, self.repository.buyer_shop_order(shop_order_id, self.principal.user_id)
        )

    def seller_product(self, product_id: int) -> int:
        shop = self.owned_shop()
        result = self._owned(product_id, self.repository.product(product_id, int(shop.shop_id)))
        self._approved(shop)
        return result

    def seller_shop_order(self, shop_order_id: int) -> int:
        shop = self.owned_shop()
        result = self._owned(
            shop_order_id, self.repository.seller_shop_order(shop_order_id, int(shop.shop_id))
        )
        if shop.shop_status not in {"APPROVED", "LOCKED"}:
            raise APIError(403, "SHOP_NOT_APPROVED", "Gian hàng chưa được phép xử lý đơn")
        return result

    def profile(self) -> UserPrivate:
        user = self.principal
        row = self.repository.shop(user.user_id)
        return UserPrivate(
            user_id=str(user.user_id),
            email=user.email,
            full_name=user.full_name,
            phone=user.phone,
            user_role=user.user_role,
            user_status=user.user_status,
            owned_shop=OwnedShop(shop_id=str(row["shop_id"]), shop_status=row["shop_status"])
            if row
            else None,
        )

    @staticmethod
    def _approved(shop: OwnedShop) -> None:
        if shop.shop_status != "APPROVED":
            raise APIError(403, "SHOP_NOT_APPROVED", "Gian hàng chưa được phép bán")

    @staticmethod
    def _valid_id(value: int) -> bool:
        return type(value) is int and 0 < value <= 9223372036854775807

    @classmethod
    def _owned(cls, requested: int, found: int | None) -> int:
        if not cls._valid_id(requested) or found is None or found != requested:
            raise APIError(404, "NOT_FOUND", "Không tìm thấy tài nguyên")
        return found
