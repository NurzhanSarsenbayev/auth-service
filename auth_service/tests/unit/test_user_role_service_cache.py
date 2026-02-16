from types import SimpleNamespace
from uuid import UUID

import pytest
from fastapi import HTTPException

from services.user_role import UserRoleService


@pytest.mark.asyncio
async def test_assign_role_to_user_rejects_duplicate():
    async def assign_role(_user_id, _role_id):
        return None  # falsy -> triggers 400

    repo = SimpleNamespace(assign_role=assign_role)
    svc = UserRoleService(repo=repo, redis=None)

    with pytest.raises(HTTPException) as e:
        await svc.assign_role_to_user(
            user_id=UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"),
            role_id=UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"),
        )

    assert e.value.status_code == 400
    assert "Role already assigned" in e.value.detail


@pytest.mark.asyncio
async def test_assign_role_to_user_updates_redis_cache(monkeypatch):
    user_id = UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
    role_id = UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")

    async def assign_role(_user_id, _role_id):
        return SimpleNamespace(id="ok")

    async def get_roles_for_user(_user_id):
        return [SimpleNamespace(name="admin"), SimpleNamespace(name="viewer")]

    repo = SimpleNamespace(assign_role=assign_role, get_roles_for_user=get_roles_for_user)

    class FakeRedis:
        def __init__(self):
            self.calls = []

        async def delete(self, key):
            self.calls.append(("delete", key))

        async def sadd(self, key, *values):
            self.calls.append(("sadd", key, values))

    redis = FakeRedis()
    svc = UserRoleService(repo=repo, redis=redis)

    result = await svc.assign_role_to_user(user_id=user_id, role_id=role_id)
    assert "assigned" in result["detail"]

    assert redis.calls[0] == ("delete", f"user_roles:{user_id}")
    assert redis.calls[1][0] == "sadd"
    assert redis.calls[1][1] == f"user_roles:{user_id}"
    assert set(redis.calls[1][2]) == {"admin", "viewer"}


@pytest.mark.asyncio
async def test_remove_role_from_user_not_found_raises():
    user_id = UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
    role_id = UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")

    async def remove_role_from_user(_user_id, _role_id):
        return SimpleNamespace(rowcount=0)

    repo = SimpleNamespace(remove_role_from_user=remove_role_from_user)
    svc = UserRoleService(repo=repo, redis=None)

    with pytest.raises(HTTPException) as e:
        await svc.remove_role_from_user(user_id=user_id, role_id=role_id)

    assert e.value.status_code == 404
    assert "Role assignment not found" in e.value.detail
