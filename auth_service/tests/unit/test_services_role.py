from types import SimpleNamespace
from uuid import UUID

import pytest
from fastapi import HTTPException

from services.role import RoleService


class FakeRole:
    def __init__(self, role_id, name, description=None):
        self.role_id = role_id
        self.name = name
        self.description = description


@pytest.mark.asyncio
async def test_create_rejects_duplicate_name():
    async def get_by_name(_name):
        return FakeRole(UUID(int=1), "admin")

    repo = SimpleNamespace(
        get_by_name=get_by_name,
        create=lambda *_a, **_k: None,  # won't be called
        list=lambda: None,
        get_by_id=lambda *_a: None,
        delete=lambda *_a: None,
        update=lambda *_a: None,
        get_role_by_name=lambda *_a: None,
    )
    svc = RoleService(repo=repo, redis=None)

    with pytest.raises(HTTPException) as e:
        await svc.create(SimpleNamespace(name="admin", description="x"))
    assert e.value.status_code == 400


@pytest.mark.asyncio
async def test_delete_raises_not_found():
    async def get_by_id(_rid):
        return None

    repo = SimpleNamespace(
        get_by_id=get_by_id,
        delete=lambda *_a: None,
        get_by_name=lambda *_a: None,
        create=lambda *_a, **_k: None,
        list=lambda *_a: None,
        update=lambda *_a: None,
        get_role_by_name=lambda *_a: None,
    )
    svc = RoleService(repo=repo, redis=None)

    with pytest.raises(HTTPException) as e:
        await svc.delete(UUID(int=2))
    assert e.value.status_code == 404


@pytest.mark.asyncio
async def test_update_rejects_name_conflict():
    role_id = UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
    other_id = UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")

    role = FakeRole(role_id, "old", "d")

    async def get_by_id(_rid):
        return role

    async def get_by_name(name):
        if name == "new":
            return FakeRole(other_id, "new")
        return None

    async def update(updated_role):
        return updated_role

    repo = SimpleNamespace(
        get_by_id=get_by_id,
        get_by_name=get_by_name,
        update=update,
        create=lambda *_a, **_k: None,
        list=lambda *_a: None,
        delete=lambda *_a: None,
        get_role_by_name=lambda *_a: None,
    )
    svc = RoleService(repo=repo, redis=None)

    with pytest.raises(HTTPException) as e:
        await svc.update(role_id, SimpleNamespace(name="new", description=None))
    assert e.value.status_code == 400


@pytest.mark.asyncio
async def test_get_guest_role_raises_if_missing():
    async def get_role_by_name(_name):
        return None

    repo = SimpleNamespace(
        get_role_by_name=get_role_by_name,
        get_by_id=lambda *_a: None,
        get_by_name=lambda *_a: None,
        create=lambda *_a, **_k: None,
        list=lambda *_a: None,
        delete=lambda *_a: None,
        update=lambda *_a: None,
    )
    svc = RoleService(repo=repo, redis=None)

    with pytest.raises(HTTPException) as e:
        await svc.get_guest_role()
    assert e.value.status_code == 500
