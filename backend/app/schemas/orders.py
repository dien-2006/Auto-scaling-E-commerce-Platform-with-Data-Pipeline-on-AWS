from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.checkout_options import PaymentMethod


class OrderQuery(BaseModel):
    model_config = ConfigDict(extra="forbid")
    page: int = Field(default=1, ge=1, le=2147483647)
    page_size: int = Field(default=24, ge=1, le=100)


class ShopOrderSummary(BaseModel):
    shop_order_id: str
    shop_id: str
    shop_name: str
    order_status: Literal["PENDING", "CONFIRMED", "SHIPPING", "COMPLETED", "CANCELLED"]
    subtotal: Decimal


class OrderSummary(BaseModel):
    order_id: str
    total_amount: Decimal
    discount_amount: Decimal = Decimal("0.00")
    shipping_fee: Decimal = Decimal("0.00")
    payment_method: PaymentMethod
    created_at: datetime
    shop_orders: list[ShopOrderSummary]


class OrderList(BaseModel):
    items: list[OrderSummary]
    page: int
    page_size: int
    total: int
