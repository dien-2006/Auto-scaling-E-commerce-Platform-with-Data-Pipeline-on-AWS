from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.orders import OrderQuery


class AdminUserQuery(OrderQuery):
    q: str = Field(default="", max_length=200)
    status: Literal["ACTIVE", "LOCKED"] | None = None


class UserStatusChange(BaseModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)
    user_status: Literal["ACTIVE", "LOCKED"]


class AdminUser(BaseModel):
    user_id: str
    email: str | None
    full_name: str
    phone: str | None
    user_role: Literal["USER", "ADMIN"]
    user_status: Literal["ACTIVE", "LOCKED"]
    created_at: datetime


class AdminUserList(BaseModel):
    items: list[AdminUser]
    page: int
    page_size: int
    total: int


class AdminUserResponse(BaseModel):
    data: AdminUser
