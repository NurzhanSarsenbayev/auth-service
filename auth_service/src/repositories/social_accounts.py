from models.social_account import SocialAccount
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select


class SocialAccountRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get(self, provider: str, provider_account_id: str) -> SocialAccount | None:
        q = await self.db.execute(
            select(SocialAccount).where(
                SocialAccount.provider == provider,
                SocialAccount.provider_account_id == provider_account_id,
            )
        )
        return q.scalar_one_or_none()

    async def link(self, user_id, provider: str, provider_account_id: str) -> SocialAccount:
        sa = SocialAccount(
            user_id=user_id,
            provider=provider,
            provider_account_id=provider_account_id,
        )
        self.db.add(sa)
        await self.db.flush()
        return sa

    async def unlink(self, user_id, provider: str) -> int:
        q = await self.db.execute(
            select(SocialAccount).where(
                SocialAccount.user_id == user_id, SocialAccount.provider == provider
            )
        )
        sa = q.scalar_one_or_none()
        if not sa:
            return 0
        await self.db.delete(sa)
        return 1
