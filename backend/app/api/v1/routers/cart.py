from typing import Annotated

from fastapi import APIRouter, Path, Response

from app.api.dependencies import ReadAccess, WriteAccess
from app.schemas.cart import CartAdd, CartQuantity, CartResponse
from app.services.cart import CartService
from app.services.storage import Storage

router = APIRouter(prefix="/cart", tags=["Buyer cart"])
ItemID = Annotated[int, Path(ge=1, le=9223372036854775807)]


@router.get("", response_model=CartResponse)
def cart(access: ReadAccess, response: Response, storage: Storage):
    response.headers["Cache-Control"] = "no-store"
    return CartResponse(data=CartService(access, storage).snapshot())


@router.post("/items", response_model=CartResponse)
def add_item(payload: CartAdd, access: WriteAccess, response: Response, storage: Storage):
    response.headers["Cache-Control"] = "no-store"
    return CartResponse(data=CartService(access, storage).add(payload.product_id, payload.quantity))


@router.patch("/items/{item_id}", response_model=CartResponse)
def update_item(
    item_id: ItemID,
    payload: CartQuantity,
    access: WriteAccess,
    response: Response,
    storage: Storage,
):
    response.headers["Cache-Control"] = "no-store"
    return CartResponse(data=CartService(access, storage).update(item_id, payload.quantity))


@router.delete("/items/{item_id}", status_code=204)
def delete_item(item_id: ItemID, access: WriteAccess, storage: Storage):
    CartService(access, storage).delete(item_id)
    return Response(status_code=204, headers={"Cache-Control": "no-store"})
