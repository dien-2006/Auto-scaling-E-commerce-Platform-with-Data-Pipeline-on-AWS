from typing import Annotated

from fastapi import APIRouter, Query, Response

from app.api.dependencies import ReadAccess, WriteAccess
from app.schemas.products import PositiveID
from app.schemas.seller_products import (
    ProductCreate,
    ProductPatch,
    SellerProductList,
    SellerProductResponse,
    SellerQuery,
)
from app.services.seller_products import SellerProductService
from app.services.storage import Storage

router = APIRouter(prefix="/seller/products", tags=["Seller products"])


@router.get("", response_model=SellerProductList)
def list_products(
    access: ReadAccess, response: Response, storage: Storage, query: Annotated[SellerQuery, Query()]
):
    response.headers["Cache-Control"] = "no-store"
    return SellerProductService(access, storage).list(query)


@router.get("/{product_id}", response_model=SellerProductResponse)
def get_product(product_id: PositiveID, access: ReadAccess, response: Response, storage: Storage):
    response.headers["Cache-Control"] = "no-store"
    return SellerProductResponse(data=SellerProductService(access, storage).detail(product_id))


@router.post("", response_model=SellerProductResponse, status_code=201)
def create_product(
    payload: ProductCreate, access: WriteAccess, response: Response, storage: Storage
):
    response.headers["Cache-Control"] = "no-store"
    return SellerProductResponse(data=SellerProductService(access, storage).create(payload))


@router.patch("/{product_id}", response_model=SellerProductResponse)
def patch_product(
    product_id: PositiveID,
    payload: ProductPatch,
    access: WriteAccess,
    response: Response,
    storage: Storage,
):
    response.headers["Cache-Control"] = "no-store"
    return SellerProductResponse(
        data=SellerProductService(access, storage).patch(product_id, payload)
    )


@router.post("/{product_id}/hide", response_model=SellerProductResponse)
def hide_product(product_id: PositiveID, access: WriteAccess, response: Response, storage: Storage):
    response.headers["Cache-Control"] = "no-store"
    return SellerProductResponse(data=SellerProductService(access, storage).hide(product_id))


@router.delete("/{product_id}", status_code=204)
def delete_product(product_id: PositiveID, access: WriteAccess, storage: Storage):
    SellerProductService(access, storage).delete(product_id)
    return Response(status_code=204, headers={"Cache-Control": "no-store"})
