from types import SimpleNamespace
from uuid import UUID

import pytest

from core.oauth.interfaces import OAuthProvider
from core.oauth.types import OAuthUserInfo
from services.oauth import OAuthService


class DummyProvider(OAuthProvider):
    name = "dummy"

    def __init__(self, authorize_url: str = "https://example/auth"):
        self._authorize_url = authorize_url

    def get_authorize_url(self, state: str | None = None) -> str:
        if state is None:
            return f"{self._authorize_url}?state=NONE"
        return f"{self._authorize_url}?state={state}"

    async def exchange_code_for_token(self, code: str) -> str:
        return f"access-token-for:{code}"

    async def get_userinfo(self, access_token: str) -> OAuthUserInfo:
        return OAuthUserInfo(
            provider="google",
            provider_account_id="acc-1",
            email="u@example.com",
            login="user1",
            name="User One",
        )


@pytest.mark.unit
def test_get_provider_unknown_raises():
    svc = OAuthService(providers={"google": DummyProvider()})
    with pytest.raises(ValueError, match="Unknown provider"):
        svc.get_provider("yandex")


@pytest.mark.unit
def test_get_authorize_url_passes_state():
    svc = OAuthService(providers={"google": DummyProvider("https://idp/auth")})
    url = svc.get_authorize_url("google", state="abc")
    assert url == "https://idp/auth?state=abc"


@pytest.mark.asyncio
async def test_handle_callback_creates_user_when_social_not_found(monkeypatch):
    provider = DummyProvider()
    svc = OAuthService(providers={"google": provider})

    # ---- fake DB ----
    class FakeDB:
        async def commit(self):
            return None

    db = FakeDB()

    # ---- fake repos used inside OAuthService ----
    class FakeSocialRepo:
        def __init__(self, _db):
            self.link_called = False

        async def get(self, prov: str, acc_id: str):
            return None  # no social link -> must create user

        async def link(self, user_id, provider, provider_account_id):
            self.link_called = True
            return None

    class FakeUserRepo:
        def __init__(self, _db):
            pass

        async def get_by_id(self, _user_id):
            return None

    # Patch constructors inside services.oauth module
    import services.oauth as oauth_module

    monkeypatch.setattr(oauth_module, "SocialAccountRepository", FakeSocialRepo)
    monkeypatch.setattr(oauth_module, "UserRepository", FakeUserRepo)

    # ---- fake user service ----
    created_user = SimpleNamespace(
        user_id=UUID("11111111-1111-1111-1111-111111111111"),
        email="u@example.com",
    )

    class FakeUserService:
        async def create_user(self, username: str, email: str, password: str):
            assert username == "user1"
            assert email == "u@example.com"
            assert password  # random uuid hex
            return created_user

    user_service = FakeUserService()

    resp = await svc.handle_callback(
        provider="google",
        code="CODE1",
        db=db,
        user_service=user_service,
    )

    assert resp.provider == "google"
    assert resp.user_id == str(created_user.user_id)
    assert resp.email == created_user.email
    assert resp.access_token
    assert resp.refresh_token
