from pydantic import BaseModel, ConfigDict, Field

from app.schemas.products import PositiveID
from app.schemas.seller_products import SellerProduct


class AdminProductQuery(BaseModel):
    model_config = ConfigDict(extra="forbid")
    q: str = Field(default="", max_length=200)
    shop_id: PositiveID | None = None
    is_active: bool | None = None
    page: int = Field(default=1, ge=1, le=2147483647)
    page_size: int = Field(default=24, ge=1, le=100)


class AdminProductList(BaseModel):
    items: list[SellerProduct]
    page: int
    page_size: int
    total: int
