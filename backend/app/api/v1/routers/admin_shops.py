from typing import Annotated

from fastapi import APIRouter, Query, Response

from app.api.dependencies import ReadAccess, WriteAccess
from app.schemas.admin_shops import AdminShopList, AdminShopQuery, ShopStatusChange
from app.schemas.products import PositiveID
from app.schemas.seller_shop import ShopResponse
from app.services.admin_shops import AdminShopService

router = APIRouter(prefix="/admin/shops", tags=["Admin shops"])


@router.get("", response_model=AdminShopList)
def shops(query: Annotated[AdminShopQuery, Query()], access: ReadAccess, response: Response):
    response.headers["Cache-Control"] = "no-store"
    return AdminShopService(access).list(query)


@router.patch("/{shop_id}/status", response_model=ShopResponse)
def status(shop_id: PositiveID, payload: ShopStatusChange, access: WriteAccess, response: Response):
    response.headers["Cache-Control"] = "no-store"
    return ShopResponse(
        data=AdminShopService(access).change(shop_id, payload.expected_status, payload.shop_status)
    )
