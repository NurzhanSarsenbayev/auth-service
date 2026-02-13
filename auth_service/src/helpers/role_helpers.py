from fastapi import HTTPException
from repositories.role import RoleRepository
from repositories.user import UserRepository


async def get_user_and_role(
    user_id: str, role_id: str, user_repo: UserRepository, role_repo: RoleRepository
) -> tuple:
    user = await user_repo.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    role = None
    if role_id:
        role = await role_repo.get_by_id(role_id)
        if not role:
            raise HTTPException(status_code=404, detail=f"Role '{role_id}' not found")
    return user, role
