import re
from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response

from app.api.dependencies import ReadAccess, WriteAccess
from app.core.errors import APIError
from app.schemas.inventory import InventoryAdjustment, InventoryResponse
from app.schemas.products import PositiveID
from app.services.inventory import InventoryService

router = APIRouter(prefix="/seller/products/{product_id}/inventory", tags=["Seller inventory"])


def expected_quantity(request: Request) -> int:
    values = request.headers.getlist("x-expected-quantity")
    if (
        len(values) != 1
        or not re.fullmatch(r"0|[1-9][0-9]{0,9}", values[0])
        or int(values[0]) > 2147483647
    ):
        raise APIError(
            422, "VALIDATION_ERROR", "Cần số lượng tồn kho đã đọc hợp lệ trong X-Expected-Quantity"
        )
    return int(values[0])


@router.get("", response_model=InventoryResponse)
def inventory(product_id: PositiveID, access: ReadAccess, response: Response):
    response.headers["Cache-Control"] = "no-store"
    return InventoryResponse(data=InventoryService(access, product_id).get())


@router.post("/adjustments", response_model=InventoryResponse)
def adjust_inventory(
    product_id: PositiveID,
    payload: InventoryAdjustment,
    access: WriteAccess,
    expected: Annotated[int, Depends(expected_quantity)],
    response: Response,
):
    response.headers["Cache-Control"] = "no-store"
    return InventoryResponse(
        data=InventoryService(access, product_id).adjust(expected, payload.delta)
    )
