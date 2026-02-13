from urllib.parse import quote

import httpx
from core.config import settings
from core.oauth.interfaces import OAuthProvider
from core.oauth.types import OAuthUserInfo

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://openidconnect.googleapis.com/v1/userinfo"


class GoogleOAuthProvider(OAuthProvider):
    name = "google"

    def get_authorize_url(self, state: str | None = None) -> str:
        if not settings.google_client_id:
            raise ValueError("GOOGLE_CLIENT_ID is required")
        redirect_uri = settings.google_redirect_uri
        if not redirect_uri:
            raise ValueError("GOOGLE_REDIRECT_URI is required")

        redirect = quote(redirect_uri, safe="")
        base = (
            f"{GOOGLE_AUTH_URL}"
            f"?response_type=code"
            f"&client_id={settings.google_client_id}"
            f"&redirect_uri={redirect}"
            f"&scope=openid%20email%20profile"
        )
        if state:
            base += f"&state={state}"
        return base

    async def exchange_code_for_token(self, code: str) -> str:
        async with httpx.AsyncClient(timeout=10) as client:
            if not settings.google_client_secret:
                raise ValueError("GOOGLE_CLIENT_SECRET is required")
            redirect_uri = settings.google_redirect_uri
            if not redirect_uri:
                raise ValueError("GOOGLE_REDIRECT_URI is required")
            resp = await client.post(
                GOOGLE_TOKEN_URL,
                data={
                    "grant_type": "authorization_code",
                    "code": code,
                    "client_id": settings.google_client_id,
                    "client_secret": settings.google_client_secret,
                    "redirect_uri": settings.google_redirect_uri,
                },
            )
        resp.raise_for_status()
        return resp.json()["access_token"]

    async def get_userinfo(self, access_token: str) -> OAuthUserInfo:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(
                GOOGLE_USERINFO_URL,
                headers={"Authorization": f"Bearer {access_token}"},
            )
        resp.raise_for_status()
        data = resp.json()
        return OAuthUserInfo(
            provider=self.name,
            provider_account_id=data["sub"],  # Google unique subject identifier
            email=data.get("email"),
            login=data.get("email"),  # Google login is typically the email
            name=data.get("name"),
        )
