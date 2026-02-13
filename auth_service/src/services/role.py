from http import HTTPStatus
from uuid import UUID

from fastapi import HTTPException
from models import Role
from schemas.role import RoleCreate, RoleUpdate
from services.base import BaseService


class RoleService(BaseService):
    async def create(self, data: RoleCreate) -> Role:
        existing = await self.repo.get_by_name(data.name)
        if existing:
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST, detail="Role with this name already exists"
            )
        return await self.repo.create(data.name, data.description)

    async def list(self) -> list[Role]:
        return await self.repo.list()

    async def delete(self, role_id: UUID) -> None:
        role = await self.repo.get_by_id(role_id)
        if not role:
            raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="Role not found")
        await self.repo.delete(role)

    async def update(self, role_id: UUID, data: RoleUpdate) -> Role:
        role = await self.repo.get_by_id(role_id)
        if not role:
            raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="Role not found")

        if data.name:
            existing = await self.repo.get_by_name(data.name)
            if existing and existing.role_id != role_id:
                raise HTTPException(
                    status_code=HTTPStatus.BAD_REQUEST, detail="Role name already exists"
                )
            role.name = data.name

        if data.description is not None:
            role.description = data.description

        return await self.repo.update(role)

    async def get_guest_role(self) -> Role:
        role = await self.repo.get_role_by_name("guest")
        if not role:
            raise HTTPException(
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR, detail="Role 'guest' not found in DB"
            )
        return role
