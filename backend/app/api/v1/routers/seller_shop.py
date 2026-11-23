from fastapi import APIRouter, Response

from app.api.dependencies import ReadAccess, WriteAccess
from app.schemas.products import PositiveID
from app.schemas.seller_shop import ShopCreate, ShopPatch, ShopResponse
from app.services.seller_shop import SellerShopService
from app.services.storage import Storage

router = APIRouter(prefix="/seller/shop", tags=["Seller shop"])


@router.get("", response_model=ShopResponse)
def get_shop(access: ReadAccess, response: Response, storage: Storage):
    response.headers["Cache-Control"] = "no-store"
    return ShopResponse(data=SellerShopService(access, storage).get())


@router.post("", response_model=ShopResponse, status_code=201)
def create_shop(payload: ShopCreate, access: WriteAccess, response: Response, storage: Storage):
    response.headers["Cache-Control"] = "no-store"
    return ShopResponse(data=SellerShopService(access, storage).create(payload))


@router.patch("", response_model=ShopResponse)
def update_shop(payload: ShopPatch, access: WriteAccess, response: Response, storage: Storage):
    response.headers["Cache-Control"] = "no-store"
    return ShopResponse(data=SellerShopService(access, storage).patch(payload))


@router.delete("/{shop_id}", status_code=204)
def delete_shop(shop_id: PositiveID, access: WriteAccess):
    SellerShopService(access).delete(shop_id)
    return Response(status_code=204, headers={"Cache-Control": "no-store"})
