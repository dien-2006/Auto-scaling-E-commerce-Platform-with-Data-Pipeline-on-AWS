from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class InventoryAdjustment(BaseModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)
    delta: int = Field(strict=True, ge=-2147483647, le=2147483647)

    @field_validator("delta")
    @classmethod
    def nonzero(cls, value: int) -> int:
        if value == 0:
            raise ValueError("Delta must not be zero")
        return value


class InventoryData(BaseModel):
    product_id: str
    quantity: int
    updated_at: datetime


class InventoryResponse(BaseModel):
    data: InventoryData
