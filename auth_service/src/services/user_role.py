from http import HTTPStatus
from uuid import UUID

from fastapi import HTTPException
from models import Role
from schemas.user import CurrentUserResponse
from schemas.user_role import UserRoleListResponse
from services.base import BaseService


class UserRoleService(BaseService):
    async def get_user_roles(self, user_id: UUID) -> list[Role]:
        """Возвращает список ролей пользователя (для RBAC и сервисов)."""
        return await self.repo.get_roles_for_user(user_id)

    async def assign_role_to_user(self, user_id: UUID, role_id: UUID) -> dict:
        """Назначает роль пользователю."""
        ur = await self.repo.assign_role(user_id, role_id)
        if not ur:
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST, detail="Role already assigned to user"
            )

        if self.redis:
            roles = await self.repo.get_roles_for_user(user_id)
            await self.redis.delete(f"user_roles:{user_id}")
            await self.redis.sadd(f"user_roles:{user_id}", *[r.name for r in roles])

        return {"detail": f"Role {role_id} assigned to user {user_id}"}

    async def remove_role_from_user(self, user_id: UUID, role_id: UUID) -> dict:
        """Удаляет роль у пользователя."""
        result = await self.repo.remove_role_from_user(user_id, role_id)
        if result.rowcount == 0:
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND, detail="Role assignment not found"
            )

        if self.redis:
            roles = await self.repo.get_roles_for_user(user_id)
            await self.redis.delete(f"user_roles:{user_id}")
            if roles:
                await self.redis.sadd(f"user_roles:{user_id}", *[r.name for r in roles])

        return {"detail": f"Role {role_id} removed from user {user_id}"}

    async def check_role(self, user_id: UUID, role_name: str) -> dict:
        """Проверяет наличие роли у пользователя."""
        roles = await self.repo.get_roles_for_user(user_id)
        allowed = any(r.name == role_name for r in roles)
        return {"allowed": allowed}

    async def current_user_info(self, principal: CurrentUserResponse) -> CurrentUserResponse:
        """Возвращает данные о текущем пользователе (или госте)."""
        return principal

    async def list_all_users(self) -> list[UserRoleListResponse]:
        """Список всех пользователей с их ролями."""
        return await self.repo.list_all()
