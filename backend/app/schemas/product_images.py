from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.core.image_limits import MAX_IMAGE_BYTES


class ImageUpload(BaseModel):
    model_config = ConfigDict(extra="forbid")
    content_type: Literal["image/jpeg", "image/png", "image/webp"]
    size_bytes: int = Field(strict=True, ge=1, le=MAX_IMAGE_BYTES)


class UploadResponse(BaseModel):
    upload_url: str
    fields: dict[str, str]
    image_key: str
    expires_at: datetime


class ImageCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    image_key: str = Field(min_length=1, max_length=200)
    is_primary: bool = Field(default=False, strict=True)
    sort_order: int = Field(default=0, strict=True, ge=0, le=2147483647)


class ImagePatch(BaseModel):
    model_config = ConfigDict(extra="forbid")
    is_primary: bool | None = Field(default=None, strict=True)
    sort_order: int | None = Field(default=None, strict=True, ge=0, le=2147483647)

    @model_validator(mode="after")
    def nonempty(self):
        if not self.model_fields_set or any(
            getattr(self, k) is None for k in self.model_fields_set
        ):
            raise ValueError("Provide non-null editable fields")
        return self


class SellerImage(BaseModel):
    product_image_id: str
    product_id: str
    image_key: str
    url: str | None
    is_primary: bool
    sort_order: int


class ImageResponse(BaseModel):
    data: SellerImage
