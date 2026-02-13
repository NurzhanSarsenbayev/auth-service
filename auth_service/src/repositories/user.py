from uuid import UUID

from models import Role, SocialAccount, User, UserRole
from repositories.base import SQLAlchemyRepository
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select


class UserRepository(SQLAlchemyRepository[User]):
    def __init__(self, session: AsyncSession):
        super().__init__(User, session)

    async def get_by_email(self, email: str) -> User | None:
        result = await self.session.execute(select(User).where(User.email == email))
        return result.scalars().first()

    async def get_by_id(self, user_id: UUID) -> User | None:
        result = await self.session.execute(select(User).where(User.user_id == user_id))
        return result.scalar_one_or_none()

    async def get_by_username(self, username: str) -> User | None:
        result = await self.session.execute(select(User).where(User.username == username))
        return result.scalars().first()

    async def get_user_roles(self, user_id: str) -> list[str]:
        result = await self.session.execute(
            select(Role.name)
            .join(UserRole, Role.role_id == UserRole.role_id)
            .where(UserRole.user_id == user_id)
        )
        return [row[0] for row in result.all()]

    async def get_by_social(self, provider: str, provider_account_id: str) -> User | None:
        """Find a user by social account"""
        result = await self.session.execute(
            select(User)
            .join(SocialAccount)
            .where(
                SocialAccount.provider == provider,
                SocialAccount.provider_account_id == provider_account_id,
            )
        )
        return result.scalars().first()

    async def link_social(
        self, user_id: UUID, provider: str, provider_account_id: str
    ) -> SocialAccount:
        """Link a social account to a user"""
        social = SocialAccount(
            user_id=user_id,
            provider=provider,
            provider_account_id=provider_account_id,
        )
        self.session.add(social)
        await self.session.flush()
        return social
