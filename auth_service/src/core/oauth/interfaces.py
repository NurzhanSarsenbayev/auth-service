from abc import ABC, abstractmethod

from .types import OAuthUserInfo


class OAuthProvider(ABC):
    name: str

    @abstractmethod
    def get_authorize_url(self, state: str | None = None) -> str: ...

    @abstractmethod
    async def exchange_code_for_token(self, code: str) -> str:
        """Return an OAuth access token."""
        ...

    @abstractmethod
    async def get_userinfo(self, access_token: str) -> OAuthUserInfo: ...
