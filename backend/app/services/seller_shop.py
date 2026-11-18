from datetime import UTC

from sqlalchemy import func
from sqlalchemy.exc import IntegrityError

from app.core.errors import APIError
from app.models import Shop
from app.repositories.seller_shop import SellerShopRepository
from app.schemas.seller_shop import ShopCreate, ShopPatch, ShopPrivate
from app.services.access import AccessPolicy


def private_shop(row: Shop) -> ShopPrivate:
    return ShopPrivate(
        shop_id=str(row.shop_id),
        owner_user_id=str(row.owner_user_id),
        shop_name=row.shop_name,
        shop_slug=row.shop_slug,
        description=row.description,
        contact_email=row.contact_email,
        shop_status=row.shop_status,
        created_at=row.created_at.astimezone(UTC),
        updated_at=row.updated_at.astimezone(UTC),
        # Delivery/upload of shop logos is not part of the current contract.
        logo_url=None,
    )


class SellerShopService:
    def __init__(self, access: AccessPolicy):
        self.repository = SellerShopRepository(access.repository.session, access.buyer().user_id)

    def get(self) -> ShopPrivate:
        row = self.repository.owned()
        if row is None:
            raise APIError(404, "NOT_FOUND", "Bạn chưa đăng ký gian hàng")
        return private_shop(row)

    def create(self, payload: ShopCreate) -> ShopPrivate:
        # WriteAccess holds the owner user lock through COMMIT. All app replicas
        # serialize registration per owner; the existing unique constraints are
        # also the final guard for writes outside this code path.
        if self.repository.owned(write=True) is not None:
            raise APIError(409, "SHOP_EXISTS", "Tài khoản đã sở hữu một gian hàng")
        try:
            row = self.repository.add(payload.model_dump())
        except IntegrityError as exc:
            constraint = getattr(getattr(exc.orig, "diag", None), "constraint_name", None)
            if getattr(exc.orig, "sqlstate", None) == "23505":
                if constraint == "shops_shop_slug_key":
                    raise APIError(
                        409, "SLUG_EXISTS", "Đường dẫn gian hàng đã được sử dụng"
                    ) from exc
                if constraint == "shops_owner_user_id_key":
                    raise APIError(409, "SHOP_EXISTS", "Tài khoản đã sở hữu một gian hàng") from exc
            raise
        return private_shop(row)

    def patch(self, payload: ShopPatch) -> ShopPrivate:
        row = self.repository.owned(write=True)
        if row is None:
            raise APIError(404, "NOT_FOUND", "Bạn chưa đăng ký gian hàng")
        for name, value in payload.model_dump(exclude_unset=True).items():
            setattr(row, name, value)
        row.updated_at = func.now()
        self.repository.session.flush()
        self.repository.session.refresh(row)
        return private_shop(row)

    def delete(self, shop_id: int) -> None:
        row = self.repository.owned(write=True)
        if row is None or row.shop_id != shop_id:
            raise APIError(404, "NOT_FOUND", "Bạn chưa đăng ký gian hàng")
        try:
            self.repository.remove(row)
        except IntegrityError as exc:
            if getattr(exc.orig, "sqlstate", None) == "23503":
                raise APIError(
                    409,
                    "SHOP_IN_USE",
                    "Gian hàng có sản phẩm hoặc lịch sử liên quan nên không thể xóa",
                ) from exc
            raise
