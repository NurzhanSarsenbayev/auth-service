import pytest
from types import SimpleNamespace
from uuid import uuid4
from unittest.mock import AsyncMock

from utils import dependencies


@pytest.mark.asyncio
async def test_build_guest_principal_uses_role_repo(monkeypatch):
    role = SimpleNamespace(role_id=uuid4(), name="guest", description="Guest role")
    session = AsyncMock()

    role_repo = SimpleNamespace(get_by_name=AsyncMock(return_value=role))
    monkeypatch.setattr(dependencies, "RoleRepository", lambda _s: role_repo)

    principal = await dependencies._build_guest_principal(session)

    assert principal.user_id is None
    assert principal.username == "guest"
    assert principal.roles
    assert principal.roles[0].name == "guest"


@pytest.mark.asyncio
async def test_build_guest_principal_fallbacks_to_db_select_when_repo_fails(monkeypatch):
    role = SimpleNamespace(role_id=uuid4(), name="guest", description="Guest role")

    role_repo = SimpleNamespace(get_by_name=AsyncMock(side_effect=RuntimeError("boom")))
    monkeypatch.setattr(dependencies, "RoleRepository", lambda _s: role_repo)

    result = SimpleNamespace(scalar_one_or_none=lambda: role)
    session = AsyncMock()
    session.execute = AsyncMock(return_value=result)

    principal = await dependencies._build_guest_principal(session)

    assert principal.user_id is None
    assert principal.username == "guest"
    assert principal.roles
    assert principal.roles[0].name == "guest"


@pytest.mark.asyncio
async def test_build_guest_principal_returns_empty_roles_when_guest_role_missing(monkeypatch):
    role_repo = SimpleNamespace(get_by_name=AsyncMock(return_value=None))
    monkeypatch.setattr(dependencies, "RoleRepository", lambda _s: role_repo)

    # important: function will fallback to DB select; stub it to return None
    result = SimpleNamespace(scalar_one_or_none=lambda: None)
    session = AsyncMock()
    session.execute = AsyncMock(return_value=result)

    principal = await dependencies._build_guest_principal(session)

    assert principal.user_id is None
    assert principal.username == "guest"
    assert principal.roles == []
