from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.orders import OrderQuery
from app.schemas.seller_shop import ShopPrivate

ShopStatus = Literal["PENDING", "APPROVED", "REJECTED", "LOCKED"]


class AdminShopQuery(OrderQuery):
    q: str = Field(default="", max_length=200)
    status: ShopStatus | None = None


class ShopStatusChange(BaseModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)
    expected_status: ShopStatus
    shop_status: ShopStatus


class AdminShopList(BaseModel):
    items: list[ShopPrivate]
    page: int
    page_size: int
    total: int
