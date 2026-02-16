from types import SimpleNamespace
from uuid import UUID

import pytest

import services.auth as auth_mod
from services.auth import AuthService


class FakeRedis:
    def __init__(self):
        self._sets: dict[str, set[object]] = {}
        self.deleted = set()

    async def sadd(self, key: str, value):
        self._sets.setdefault(key, set()).add(value)

    async def srem(self, key: str, value):
        self._sets.setdefault(key, set()).discard(value)

    async def smembers(self, key: str):
        return self._sets.get(key, set())

    async def delete(self, key: str):
        self.deleted.add(key)
        self._sets.pop(key, None)


@pytest.mark.asyncio
async def test_refresh_by_cookie_rotates_and_revokes_old(monkeypatch):
    session = object()
    repo = SimpleNamespace(session=session)
    redis = FakeRedis()
    svc = AuthService(repo=repo, redis=redis)

    user_id = UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
    old_refresh = "old-rt"

    async def fake_validate_refresh(_rt, _session, _redis, _svc):
        return SimpleNamespace(user_id=user_id)

    async def fake_blacklist(_redis, token):
        await _redis.sadd("blacklist", token)

    def fake_issue_tokens(_user):
        return SimpleNamespace(access_token="new-at", refresh_token="new-rt", token_type="bearer")

    monkeypatch.setattr(auth_mod, "validate_refresh", fake_validate_refresh)
    monkeypatch.setattr(auth_mod, "blacklist_token", fake_blacklist)
    monkeypatch.setattr(auth_mod, "issue_tokens", fake_issue_tokens)

    # pre-track old token
    await redis.sadd(f"user_refresh:{user_id}", old_refresh)

    tokens = await svc.refresh_by_cookie(old_refresh)

    # old revoked
    assert "old-rt" in await redis.smembers("blacklist")
    assert old_refresh not in await redis.smembers(f"user_refresh:{user_id}")

    # new tracked
    assert "new-rt" in await redis.smembers(f"user_refresh:{user_id}")
    assert tokens.refresh_token == "new-rt"


@pytest.mark.asyncio
async def test_logout_all_decodes_bytes(monkeypatch):
    session = object()
    repo = SimpleNamespace(session=session)
    redis = FakeRedis()
    svc = AuthService(repo=repo, redis=redis)

    user_id = UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")
    await redis.sadd(f"user_refresh:{user_id}", b"t1")
    await redis.sadd(f"user_refresh:{user_id}", "t2")

    async def fake_blacklist(_redis, token):
        await _redis.sadd("blacklist", token)

    monkeypatch.setattr(auth_mod, "blacklist_token", fake_blacklist)

    await svc.logout_all(user_id)

    bl = await redis.smembers("blacklist")
    assert "t1" in bl
    assert "t2" in bl
    assert f"user_refresh:{user_id}" in redis.deleted
