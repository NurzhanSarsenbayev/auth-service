import pytest
from types import SimpleNamespace
from uuid import uuid4
from unittest.mock import AsyncMock

from utils import dependencies


@pytest.mark.asyncio
async def test_get_user_from_token_returns_none_when_token_missing():
    user = await dependencies._get_user_from_token(
        token=None,
        session=AsyncMock(),
        redis=AsyncMock(),
    )
    assert user is None


@pytest.mark.asyncio
async def test_get_user_from_token_returns_none_when_decode_fails(monkeypatch):
    async def bad_decode(_token, *, redis):
        raise ValueError("bad token")

    monkeypatch.setattr(dependencies, "decode_token", bad_decode)

    user = await dependencies._get_user_from_token(
        token="t",
        session=AsyncMock(),
        redis=AsyncMock(),
    )
    assert user is None


@pytest.mark.asyncio
async def test_get_user_from_token_returns_none_when_not_access_token(monkeypatch):
    async def ok_decode(_token, *, redis):
        return {"type": "refresh", "sub": str(uuid4())}

    monkeypatch.setattr(dependencies, "decode_token", ok_decode)

    user = await dependencies._get_user_from_token(
        token="t",
        session=AsyncMock(),
        redis=AsyncMock(),
    )
    assert user is None


@pytest.mark.asyncio
async def test_get_user_from_token_returns_none_when_user_not_found(monkeypatch):
    async def ok_decode(_token, *, redis):
        return {"type": "access", "sub": str(uuid4())}

    monkeypatch.setattr(dependencies, "decode_token", ok_decode)

    result = SimpleNamespace(scalar_one_or_none=lambda: None)
    session = AsyncMock()
    session.execute = AsyncMock(return_value=result)

    user = await dependencies._get_user_from_token(
        token="t",
        session=session,
        redis=AsyncMock(),
    )
    assert user is None


@pytest.mark.asyncio
async def test_get_user_from_token_success(monkeypatch):
    uid = uuid4()

    async def ok_decode(_token, *, redis):
        return {"type": "access", "sub": str(uid)}

    monkeypatch.setattr(dependencies, "decode_token", ok_decode)

    user_obj = SimpleNamespace(user_id=uid, username="kate", email="kate@example.com")
    result = SimpleNamespace(scalar_one_or_none=lambda: user_obj)

    session = AsyncMock()
    session.execute = AsyncMock(return_value=result)

    user = await dependencies._get_user_from_token(
        token="t",
        session=session,
        redis=AsyncMock(),
    )

    assert user.user_id == uid
    assert user.username == "kate"
    assert user.email == "kate@example.com"
