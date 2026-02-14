from http import HTTPStatus

from fastapi import HTTPException
from fastapi_pagination import Page, Params
from fastapi_pagination.ext.sqlalchemy import apaginate
from models import LoginHistory, Role, User, UserRole
from schemas.user import (
    UserUpdateRequest,
    UserUpdateResponse,
)
from services.base import BaseService
from sqlalchemy import select
from utils.security import hash_password, verify_password


class UserService(BaseService):
    async def get_user_by_id(self, user_id: str) -> User | None:
        return await self.repo.get_by_id(user_id)

    async def get_user_by_email(self, email: str) -> User | None:
        return await self.repo.get_by_email(email)

    async def get_user_by_username(self, username: str) -> User | None:
        return await self.repo.get_by_username(username)

    async def create_user(self, username: str, email: str, password: str) -> User:
        if await self.repo.get_by_email(email):
            raise HTTPException(
                HTTPStatus.BAD_REQUEST,
                "Email already registered",
            )
        if await self.repo.get_by_username(username):
            raise HTTPException(
                HTTPStatus.BAD_REQUEST,
                "Username already taken",
            )

        hashed_pwd = hash_password(password)
        user = User(username=username, email=email, hashed_password=hashed_pwd)
        self.repo.session.add(user)
        await self.repo.session.flush()

        result = await self.repo.session.execute(select(Role).where(Role.name == "user"))
        default_role = result.scalar_one_or_none()
        if default_role:
            self.repo.session.add(UserRole(user_id=user.user_id, role_id=default_role.role_id))

        await self.repo.session.commit()
        await self.repo.session.refresh(user)
        return user

    async def get_login_history(self, user_id: str, params: Params) -> Page[LoginHistory]:
        """Login history with pagination (returns ORM objects)."""
        stmt = (
            select(LoginHistory)
            .where(LoginHistory.user_id == user_id)
            .order_by(LoginHistory.login_time.desc())
        )
        return await apaginate(self.repo.session, stmt, params)

    async def update_user(
        self, current_user: User, update: UserUpdateRequest
    ) -> UserUpdateResponse:
        updated = False

        if update.username:
            stmt = select(User).where(
                User.username == update.username,
                User.user_id != current_user.user_id,
            )
            result = await self.repo.session.execute(stmt)
            if result.scalar_one_or_none():
                raise HTTPException(
                    HTTPStatus.BAD_REQUEST,
                    "Username already taken",
                )
            current_user.username = update.username
            updated = True

        if update.old_password and update.new_password:
            if verify_password(update.old_password, current_user.hashed_password):
                current_user.hashed_password = hash_password(update.new_password)
                updated = True
            else:
                raise HTTPException(HTTPStatus.BAD_REQUEST, "Wrong password")

        if not updated:
            raise HTTPException(
                HTTPStatus.BAD_REQUEST,
                "No changes provided. Please specify username or password update.",
            )

        await self.repo.session.commit()
        await self.repo.session.refresh(current_user)
        return UserUpdateResponse(message="User data updated successfully")

    async def delete_user(self, user_id: str):
        user = await self.repo.get_by_id(user_id)
        if not user:
            raise HTTPException(HTTPStatus.NOT_FOUND, "User not found")
        await self.repo.session.delete(user)
        await self.repo.session.commit()
        return {"detail": "User deleted successfully"}
