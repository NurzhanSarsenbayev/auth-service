from uuid import UUID

from pydantic import BaseModel, Field
from schemas.role import RoleResponse


# ----- list of users with roles (admin only) -----
class UserRoleListResponse(BaseModel):
    user_id: UUID = Field(alias="id")
    username: str
    roles: list[RoleResponse] = []

    class Config:
        from_attributes = True  # allow ORM -> Pydantic mapping
        populate_by_name = True
