from datetime import datetime
from decimal import Decimal
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field

PositiveID = Annotated[int, Field(ge=1, le=9223372036854775807)]


class ProductQuery(BaseModel):
    model_config = ConfigDict(extra="forbid")

    q: str = Field(default="", max_length=200)
    category_id: PositiveID | None = None
    shop_id: PositiveID | None = None
    page: int = Field(default=1, ge=1, le=2147483647)
    page_size: int = Field(default=24, ge=1, le=100)
    sort: Literal["newest", "price_asc", "price_desc"] = "newest"


class ProductShop(BaseModel):
    shop_id: str
    shop_name: str
    shop_slug: str


class ProductSummary(BaseModel):
    product_id: str
    product_name: str
    price: Decimal
    currency: Literal["VND"] = "VND"
    primary_image_url: str | None = None
    shop: ProductShop
    category_id: str
    in_stock: bool


class PublicProductImage(BaseModel):
    product_image_id: str
    url: str | None = None
    is_primary: bool
    sort_order: int


class ProductDetail(ProductSummary):
    description: str | None
    sku: str
    images: list[PublicProductImage]
    available_quantity: int


class ProductList(BaseModel):
    items: list[ProductSummary]
    page: int
    page_size: int
    total: int


class ProductResponse(BaseModel):
    data: ProductDetail


class DealSummary(ProductSummary):
    original_price: Decimal
    sale_price: Decimal
    discount_percent: Decimal
    coupon_code: str | None = None
    ends_at: datetime | None = None


class DealList(BaseModel):
    items: list[DealSummary]


class BestsellerList(BaseModel):
    items: list[ProductSummary]
    ranked: bool
