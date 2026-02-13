import secrets
import uuid

from core.oauth.interfaces import OAuthProvider
from core.oauth.types import OAuthUserInfo
from repositories.social_accounts import SocialAccountRepository
from repositories.user import UserRepository
from schemas.oauth import OAuthCallbackResponse
from services.user import UserService
from sqlalchemy.ext.asyncio import AsyncSession
from utils.jwt import create_access_token, create_refresh_token


class OAuthService:
    def __init__(self, providers: dict[str, OAuthProvider]):
        self.providers = providers

    def get_provider(self, name: str) -> OAuthProvider:
        if name not in self.providers:
            raise ValueError(f"Unknown provider: {name}")
        return self.providers[name]

    def get_authorize_url(self, provider: str, state: str | None = None) -> str:
        if state is None:
            state = secrets.token_urlsafe(16)
        return self.get_provider(provider).get_authorize_url(state=state)

    async def handle_callback(
        self,
        provider: str,
        code: str,
        db: AsyncSession,
        user_service: UserService,  # ⬅️ приняли сервис
    ) -> OAuthCallbackResponse:
        prov = self.get_provider(provider)

        access_token = await prov.exchange_code_for_token(code)
        info: OAuthUserInfo = await prov.get_userinfo(access_token)

        users = UserRepository(db)
        socials = SocialAccountRepository(db)

        social = await socials.get(info.provider, info.provider_account_id)
        if social:
            user = await users.get_by_id(social.user_id)
        else:
            # если email нет — даём детерминированный fallback
            username = info.login or f"user_{info.provider_account_id}"
            email = info.email or f"{username}@no-email.local"

            # ✅ создаём через UserService → роль `user` навесится автоматически
            user = await user_service.create_user(
                username=username,
                email=email,
                password=uuid.uuid4().hex,  # пароль не используется при OAuth
            )

            await socials.link(
                user_id=user.user_id,
                provider=info.provider,
                provider_account_id=info.provider_account_id,
            )

        await db.commit()

        payload = {"sub": str(user.user_id), "email": user.email}
        return OAuthCallbackResponse(  # ✅ красиво и типизировано
            user_id=str(user.user_id),
            email=user.email,
            access_token=create_access_token(payload),
            refresh_token=create_refresh_token(payload),
            provider=provider,
        )

    async def unlink(self, provider: str, user_id: uuid.UUID, db: AsyncSession):
        socials = SocialAccountRepository(db)
        await socials.unlink(user_id=user_id, provider=provider)
        await db.commit()
