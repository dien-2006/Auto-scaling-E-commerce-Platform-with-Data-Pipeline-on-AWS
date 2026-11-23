from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.schemas.cart import CartAdd
from app.schemas.catalog import CategoryTree
from app.schemas.products import PositiveID


class CategoryCreate(BaseModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)
    category_name: str = Field(min_length=1, max_length=120)
    category_slug: str = Field(min_length=1, max_length=140, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    parent_category_id: PositiveID | None = None
    is_active: bool = Field(default=True, strict=True)

    @field_validator("category_name", "category_slug", mode="before")
    @classmethod
    def trim(cls, value):
        return value.strip() if isinstance(value, str) else value

    @field_validator("parent_category_id", mode="before")
    @classmethod
    def exact_parent(cls, value):
        return None if value is None else CartAdd.exact_id(value)


class CategoryPatch(BaseModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)
    category_name: str | None = Field(default=None, min_length=1, max_length=120)
    category_slug: str | None = Field(
        default=None, min_length=1, max_length=140, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$"
    )
    parent_category_id: PositiveID | None = None
    is_active: bool | None = Field(default=None, strict=True)
    _trim = field_validator("category_name", "category_slug", mode="before")(
        CategoryCreate.trim.__func__
    )
    _parent = field_validator("parent_category_id", mode="before")(
        CategoryCreate.exact_parent.__func__
    )

    @model_validator(mode="after")
    def nonempty(self):
        if not self.model_fields_set or any(
            getattr(self, field) is None for field in self.model_fields_set - {"parent_category_id"}
        ):
            raise ValueError("Provide fields; only parent_category_id may be null")
        return self


class CategoryResponse(BaseModel):
    data: CategoryTree
