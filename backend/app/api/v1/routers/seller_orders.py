from typing import Annotated

from fastapi import APIRouter, Query, Response

from app.api.dependencies import ReadAccess, WriteAccess
from app.schemas.products import PositiveID
from app.schemas.seller_orders import (
    SellerOrderList,
    SellerOrderQuery,
    SellerOrderResponse,
    StatusChange,
)
from app.services.seller_orders import SellerOrderService

router = APIRouter(tags=["Seller orders"])


@router.get("/seller/orders", response_model=SellerOrderList)
def orders(query: Annotated[SellerOrderQuery, Query()], access: ReadAccess, response: Response):
    response.headers["Cache-Control"] = "no-store"
    return SellerOrderService(access).list(query)


@router.get("/seller/orders/{sid}", response_model=SellerOrderResponse)
def detail(sid: PositiveID, access: ReadAccess, response: Response):
    response.headers["Cache-Control"] = "no-store"
    return SellerOrderResponse(data=SellerOrderService(access).detail(sid))


@router.patch("/seller/orders/{sid}/status", response_model=SellerOrderResponse)
def status(sid: PositiveID, payload: StatusChange, access: WriteAccess, response: Response):
    response.headers["Cache-Control"] = "no-store"
    return SellerOrderResponse(
        data=SellerOrderService(access).change(sid, payload.status, payload.expected_status)
    )


@router.post("/orders/{order_id}/shop-orders/{sid}/cancel", response_model=SellerOrderResponse)
def cancel(order_id: PositiveID, sid: PositiveID, access: WriteAccess, response: Response):
    response.headers["Cache-Control"] = "no-store"
    return SellerOrderResponse(
        data=SellerOrderService(access, buyer=True).change(sid, "CANCELLED", order_id=order_id)
    )
