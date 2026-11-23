from typing import Annotated

from fastapi import APIRouter, Path, Query, Response

from app.api.dependencies import ReadAccess
from app.schemas.checkout import CheckoutResponse
from app.schemas.orders import OrderList, OrderQuery
from app.services.orders import OrderService

router = APIRouter(prefix="/orders", tags=["Buyer orders"])


@router.get("", response_model=OrderList)
def orders(query: Annotated[OrderQuery, Query()], access: ReadAccess, response: Response):
    response.headers["Cache-Control"] = "no-store"
    return OrderService(access).list(query)


@router.get("/{order_id}", response_model=CheckoutResponse)
def order(
    order_id: Annotated[int, Path(ge=1, le=9223372036854775807)],
    access: ReadAccess,
    response: Response,
):
    response.headers["Cache-Control"] = "no-store"
    return CheckoutResponse(data=OrderService(access).detail(order_id))
