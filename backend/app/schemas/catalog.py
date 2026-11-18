from pydantic import BaseModel, Field


class CategoryTree(BaseModel):
    category_id: str
    parent_category_id: str | None
    category_name: str
    category_slug: str
    is_active: bool
    children: list["CategoryTree"] = Field(default_factory=list)


class CategoryList(BaseModel):
    items: list[CategoryTree]


class ShopPublic(BaseModel):
    shop_id: str
    shop_name: str
    shop_slug: str
    description: str | None
    logo_url: str | None = None


class ShopResponse(BaseModel):
    data: ShopPublic
