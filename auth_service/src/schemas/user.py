from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field
from schemas.role import RoleResponse


class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str = Field(..., min_length=3)


class UserRead(BaseModel):
    user_id: UUID
    username: str
    email: EmailStr
    is_active: bool

    model_config = {
        "from_attributes": True,
    }


class UserResponse(BaseModel):
    user_id: UUID = Field(alias="id")
    username: str
    roles: list[RoleResponse] = Field(default_factory=list)

    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
    }


class CurrentUserResponse(BaseModel):
    user_id: UUID | None = Field(alias="id", default=None)
    username: str
    email: EmailStr | None = None
    roles: list[RoleResponse] = Field(default_factory=list)

    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
    }


# ----- auth/history -----
class LoginHistoryItem(BaseModel):
    user_id: UUID
    login_time: datetime
    ip_address: str | None = None
    user_agent: str | None = None
    successful: bool

    model_config = {
        "from_attributes": True,
    }


# ----- auth/update -----
class UserUpdateRequest(BaseModel):
    username: str | None = Field(None, min_length=3, max_length=50)
    old_password: str | None = Field(None, min_length=3, max_length=50)
    new_password: str | None = Field(None, min_length=3)


class UserUpdateResponse(BaseModel):
    message: str
