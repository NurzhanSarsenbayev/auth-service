import pytest
from types import SimpleNamespace
from uuid import uuid4
from unittest.mock import AsyncMock

from fastapi import HTTPException

from utils import dependencies


@pytest.mark.asyncio
async def test_get_current_principal_returns_guest_when_token_missing(monkeypatch):
    guest = SimpleNamespace(user_id=None, username="guest", email=None, roles=[])
    monkeypatch.setattr(dependencies, "_build_guest_principal", AsyncMock(return_value=guest))

    out = await dependencies.get_current_principal(
        session=AsyncMock(),
        redis_cli=AsyncMock(),
        token=None,
    )

    assert out.user_id is None
    assert out.username == "guest"


@pytest.mark.asyncio
async def test_get_current_principal_returns_guest_when_decode_fails(monkeypatch):
    guest = SimpleNamespace(user_id=None, username="guest", email=None, roles=[])
    monkeypatch.setattr(dependencies, "_build_guest_principal", AsyncMock(return_value=guest))

    async def bad_decode(_token, *, redis):
        raise ValueError("bad token")

    monkeypatch.setattr(dependencies, "decode_token", bad_decode)

    out = await dependencies.get_current_principal(
        session=AsyncMock(),
        redis_cli=AsyncMock(),
        token="t",
    )

    assert out.user_id is None
    assert out.username == "guest"


@pytest.mark.asyncio
async def test_get_current_principal_returns_user_when_token_ok(monkeypatch):
    uid = uuid4()

    async def ok_decode(_token, *, redis):
        return {"type": "access", "sub": str(uid)}

    monkeypatch.setattr(dependencies, "decode_token", ok_decode)

    user_obj = SimpleNamespace(user_id=uid, username="kate", email="kate@example.com")
    role_obj = SimpleNamespace(role_id=uuid4(), name="admin", description="Admin")

    user_repo = SimpleNamespace(get_by_id=AsyncMock(return_value=user_obj))
    ur_repo = SimpleNamespace(get_roles_for_user=AsyncMock(return_value=[role_obj]))

    monkeypatch.setattr(dependencies, "UserRepository", lambda _s: user_repo)
    monkeypatch.setattr(dependencies, "UserRoleRepository", lambda _s: ur_repo)

    out = await dependencies.get_current_principal(
        session=AsyncMock(),
        redis_cli=AsyncMock(),
        token="t",
    )

    assert out.user_id == uid
    assert out.username == "kate"
    assert out.roles
    assert out.roles[0].name == "admin"


@pytest.mark.asyncio
async def test_get_current_user_with_roles_raises_401_when_user_none(monkeypatch):
    async def no_user(*_args, **_kwargs):
        return None

    monkeypatch.setattr(dependencies, "_get_user_from_token", no_user)

    dep = dependencies.get_current_user_with_roles(["admin"])

    with pytest.raises(HTTPException) as e:
        await dep(
            token="t",
            session=AsyncMock(),
            redis=AsyncMock(),
        )

    assert e.value.status_code == 401


@pytest.mark.asyncio
async def test_get_current_user_with_roles_raises_403_when_missing_role(monkeypatch):
    uid = uuid4()
    user_obj = SimpleNamespace(user_id=uid, username="kate", email="kate@example.com")

    async def ok_user(*_args, **_kwargs):
        return user_obj

    monkeypatch.setattr(dependencies, "_get_user_from_token", ok_user)

    # user has only "user" role, but required is "admin"
    role_user = SimpleNamespace(name="user")
    user_role_svc = SimpleNamespace(get_user_roles=AsyncMock(return_value=[role_user]))

    monkeypatch.setattr(dependencies, "UserRoleService", lambda repo, redis: user_role_svc)
    monkeypatch.setattr(dependencies, "UserRoleRepository", lambda _s: object())

    dep = dependencies.get_current_user_with_roles(["admin"])

    with pytest.raises(HTTPException) as e:
        await dep(
            token="t",
            session=AsyncMock(),
            redis=AsyncMock(),
        )

    assert e.value.status_code == 403


@pytest.mark.asyncio
async def test_get_current_user_with_roles_allows_when_role_present(monkeypatch):
    uid = uuid4()
    user_obj = SimpleNamespace(user_id=uid, username="kate", email="kate@example.com")

    async def ok_user(*_args, **_kwargs):
        return user_obj

    monkeypatch.setattr(dependencies, "_get_user_from_token", ok_user)

    role_admin = SimpleNamespace(name="admin")
    user_role_svc = SimpleNamespace(get_user_roles=AsyncMock(return_value=[role_admin]))

    monkeypatch.setattr(dependencies, "UserRoleService", lambda repo, redis: user_role_svc)
    monkeypatch.setattr(dependencies, "UserRoleRepository", lambda _s: object())

    dep = dependencies.get_current_user_with_roles(["admin"])

    out = await dep(
        token="t",
        session=AsyncMock(),
        redis=AsyncMock(),
    )

    assert out.user_id == uid
