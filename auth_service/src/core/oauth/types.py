from dataclasses import dataclass


@dataclass(frozen=True)
class OAuthUserInfo:
    provider: str  # "yandex"
    provider_account_id: str  # FastAPI dependency provider
    email: str | None
    login: str | None
    name: str | None = None
