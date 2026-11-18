from typing import Annotated

from fastapi import APIRouter, Query, Response

from app.api.dependencies import ReadAccess, WriteAccess
from app.schemas.admin_products import AdminProductList, AdminProductQuery
from app.schemas.products import PositiveID
from app.schemas.seller_products import SellerProductResponse
from app.services.admin_products import AdminProductService
from app.services.storage import Storage

router = APIRouter(prefix="/admin/products", tags=["Admin products"])


@router.get("", response_model=AdminProductList)
def products(
    access: ReadAccess,
    response: Response,
    storage: Storage,
    query: Annotated[AdminProductQuery, Query()],
):
    response.headers["Cache-Control"] = "no-store"
    return AdminProductService(access, storage).list(query)


@router.post("/{product_id}/hide", response_model=SellerProductResponse)
def hide(product_id: PositiveID, access: WriteAccess, response: Response, storage: Storage):
    response.headers["Cache-Control"] = "no-store"
    return SellerProductResponse(data=AdminProductService(access, storage).hide(product_id))
