import pytest
from types import SimpleNamespace
from uuid import uuid4
from unittest.mock import AsyncMock

from fastapi import HTTPException

from utils import dependencies


@pytest.mark.asyncio
async def test_get_user_from_token_raises_401_when_decode_fails(monkeypatch):
    async def bad_decode(_token, _pub_key):
        raise ValueError("bad token")

    monkeypatch.setattr(dependencies, "decode_token", bad_decode)

    session = AsyncMock()
    with pytest.raises(HTTPException) as e:
        await dependencies._get_user_from_token(session, "t", "pub")

    assert e.value.status_code == 401


@pytest.mark.asyncio
async def test_get_user_from_token_raises_401_when_payload_missing_sub(monkeypatch):
    async def ok_decode(_token, _pub_key):
        return {"email": "x@example.com"}  # no "sub"

    monkeypatch.setattr(dependencies, "decode_token", ok_decode)

    session = AsyncMock()
    with pytest.raises(HTTPException) as e:
        await dependencies._get_user_from_token(session, "t", "pub")

    assert e.value.status_code == 401


@pytest.mark.asyncio
async def test_get_user_from_token_raises_401_when_user_not_found(monkeypatch):
    uid = str(uuid4())

    async def ok_decode(_token, _pub_key):
        return {"sub": uid, "email": "x@example.com"}

    monkeypatch.setattr(dependencies, "decode_token", ok_decode)

    # session.execute(...) -> result.scalar_one_or_none() -> None
    result = SimpleNamespace(scalar_one_or_none=lambda: None)
    session = AsyncMock()
    session.execute = AsyncMock(return_value=result)

    with pytest.raises(HTTPException) as e:
        await dependencies._get_user_from_token(session, "t", "pub")

    assert e.value.status_code == 401


@pytest.mark.asyncio
async def test_get_user_from_token_success(monkeypatch):
    uid = uuid4()

    async def ok_decode(_token, _pub_key):
        return {"sub": str(uid), "email": "kate@example.com"}

    monkeypatch.setattr(dependencies, "decode_token", ok_decode)

    user_obj = SimpleNamespace(id=uid, username="kate", email="kate@example.com")
    result = SimpleNamespace(scalar_one_or_none=lambda: user_obj)

    session = AsyncMock()
    session.execute = AsyncMock(return_value=result)

    user = await dependencies._get_user_from_token(session, "t", "pub")

    assert user.user_id == uid
    assert user.username == "kate"
    assert user.email == "kate@example.com"
