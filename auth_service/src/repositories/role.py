# src/repositories/role_repo.py

import builtins

from models import Role, UserRole
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


class RoleRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, name: str, description: str | None = None) -> Role:
        role = Role(name=name, description=description)
        self.session.add(role)
        await self.session.commit()
        await self.session.refresh(role)
        return role

    async def list(self) -> list[Role]:
        q = await self.session.execute(select(Role))
        return q.scalars().all()

    async def get_by_id(self, role_id):
        return await self.session.get(Role, role_id)

    async def get_by_name(self, name: str):
        q = await self.session.execute(select(Role).where(Role.name == name))
        return q.scalar_one_or_none()

    async def update(self, role: Role, **kwargs):
        for k, v in kwargs.items():
            setattr(role, k, v)
        self.session.add(role)
        await self.session.commit()
        await self.session.refresh(role)
        return role

    async def delete(self, role: Role):
        await self.session.delete(role)
        await self.session.commit()

    async def remove_role(self, user_id, role_id):
        q = await self.session.execute(
            select(UserRole).where(UserRole.user_id == user_id, UserRole.role_id == role_id)
        )
        user_role = q.scalar_one_or_none()
        if user_role:
            await self.session.delete(user_role)
            await self.session.commit()
            return True
        return False

    async def get_user_roles(self, user_id) -> builtins.list[str]:
        q = await self.session.execute(
            select(Role.name)
            .join(UserRole, UserRole.role_id == Role.role_id)
            .where(UserRole.user_id == user_id)
        )
        return [r[0] for r in q.all()]

    async def get_role_by_name(self, name: str):
        query = select(Role).where(Role.name == name)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
