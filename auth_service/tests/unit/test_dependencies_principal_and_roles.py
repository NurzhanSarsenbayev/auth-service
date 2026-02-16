import pytest
from types import SimpleNamespace
from uuid import uuid4
from unittest.mock import AsyncMock

from fastapi import HTTPException

from utils import dependencies
from schemas.user import CurrentUserResponse
from schemas.role import RoleResponse


@pytest.mark.asyncio
async def test_get_current_principal_returns_guest_when_no_user(monkeypatch):
    session = AsyncMock()

    async def no_user(_s, _t, _p):
        return None

    async def guest(_s):
        return dependencies.Principal(user=None, roles=[])

    monkeypatch.setattr(dependencies, "_get_user_from_token", no_user)
    monkeypatch.setattr(dependencies, "_build_guest_principal", guest)

    principal = await dependencies.get_current_principal(session=session, token=None, public_key="pk")

    assert principal.user is None


@pytest.mark.asyncio
async def test_get_current_principal_returns_user_when_token_ok(monkeypatch):
    session = AsyncMock()
    uid = uuid4()
    user = CurrentUserResponse(id=uid, username="kate", email="kate@example.com", roles=[])

    async def ok_user(_s, _t, _p):
        return user

    monkeypatch.setattr(dependencies, "_get_user_from_token", ok_user)

    principal = await dependencies.get_current_principal(session=session, token="t", public_key="pk")

    assert principal.user is not None
    assert principal.user.user_id == uid


@pytest.mark.asyncio
async def test_get_current_user_with_roles_raises_401_when_user_none(monkeypatch):
    # make get_current_principal return guest principal
    async def guest_principal(*_args, **_kwargs):
        return dependencies.Principal(user=None, roles=[])

    monkeypatch.setattr(dependencies, "get_current_principal", guest_principal)

    with pytest.raises(HTTPException) as e:
        await dependencies.get_current_user_with_roles(session=AsyncMock(), token=None, public_key="pk")

    assert e.value.status_code == 401


@pytest.mark.asyncio
async def test_get_current_user_with_roles_fetches_roles(monkeypatch):
    session = AsyncMock()
    uid = uuid4()

    principal = dependencies.Principal(
        user=CurrentUserResponse(id=uid, username="kate", email="kate@example.com", roles=[]),
        roles=[],
    )

    async def ok_principal(*_args, **_kwargs):
        return principal

    # user roles service returns roles
    role = RoleResponse(id=uuid4(), name="admin", description="Admin")
    user_role_svc = SimpleNamespace(get_user_roles=AsyncMock(return_value=[role]))

    monkeypatch.setattr(dependencies, "get_current_principal", ok_principal)
    monkeypatch.setattr(dependencies, "UserRoleService", lambda repo, redis: user_role_svc)
    monkeypatch.setattr(dependencies, "UserRoleRepository", lambda _s: object())
    monkeypatch.setattr(dependencies, "get_redis", lambda: None)

    user = await dependencies.get_current_user_with_roles(session=session, token="t", public_key="pk")

    assert user.user_id == uid
    assert user.roles
    assert user.roles[0].name == "admin"


def test_require_roles_raises_403_when_missing_role():
    uid = uuid4()
    principal = dependencies.Principal(
        user=CurrentUserResponse(id=uid, username="kate", email="kate@example.com", roles=[]),
        roles=[RoleResponse(id=uuid4(), name="user", description="User")],
    )

    checker = dependencies.require_roles(["admin"])

    with pytest.raises(HTTPException) as e:
        checker(principal)

    assert e.value.status_code == 403


def test_require_roles_allows_when_role_present():
    uid = uuid4()
    principal = dependencies.Principal(
        user=CurrentUserResponse(id=uid, username="kate", email="kate@example.com", roles=[]),
        roles=[RoleResponse(id=uuid4(), name="admin", description="Admin")],
    )

    checker = dependencies.require_roles(["admin"])
    out = checker(principal)

    assert out.user.user_id == uid
