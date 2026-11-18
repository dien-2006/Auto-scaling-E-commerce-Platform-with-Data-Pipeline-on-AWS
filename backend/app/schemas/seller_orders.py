from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict

from app.schemas.checkout import OrderLineData
from app.schemas.checkout_options import PaymentMethod
from app.schemas.orders import OrderQuery

OrderStatus = Literal["PENDING", "CONFIRMED", "SHIPPING", "COMPLETED", "CANCELLED"]


class SellerOrderQuery(OrderQuery):
    status: OrderStatus | None = None


class StatusChange(BaseModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)
    expected_status: OrderStatus
    status: OrderStatus


class SellerOrderSummary(BaseModel):
    shop_order_id: str
    order_id: str
    shop_id: str
    order_status: OrderStatus
    subtotal: Decimal
    created_at: datetime
    updated_at: datetime


class SellerOrderDetail(SellerOrderSummary):
    buyer_name: str | None = None
    recipient_name: str
    phone: str
    shipping_address: str
    payment_method: PaymentMethod
    items: list[OrderLineData]


class SellerOrderResponse(BaseModel):
    data: SellerOrderDetail


class SellerOrderList(BaseModel):
    items: list[SellerOrderSummary]
    page: int
    page_size: int
    total: int
