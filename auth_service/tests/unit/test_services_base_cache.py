import pytest

from services.base import BaseService


class FakeRedis:
    def __init__(self):
        self._sets: dict[str, set[object]] = {}

    async def smembers(self, key: str):
        return self._sets.get(key, set())

    async def sadd(self, key: str, *values):
        self._sets.setdefault(key, set()).update(values)

    async def srem(self, key: str, value):
        self._sets.setdefault(key, set()).discard(value)


@pytest.mark.asyncio
async def test_get_cached_list_returns_none_when_no_redis():
    svc = BaseService(repo=object(), redis=None)
    assert await svc.get_cached_list("k") is None


@pytest.mark.asyncio
async def test_get_cached_list_decodes_bytes_and_keeps_strings():
    r = FakeRedis()
    await r.sadd("k", b"a", "b")
    svc = BaseService(repo=object(), redis=r)

    got = await svc.get_cached_list("k")
    assert sorted(got) == ["a", "b"]


@pytest.mark.asyncio
async def test_set_cache_list_noop_when_values_empty():
    r = FakeRedis()
    svc = BaseService(repo=object(), redis=r)

    await svc.set_cache_list("k", [])
    assert await svc.get_cached_list("k") is None


@pytest.mark.asyncio
async def test_set_cache_list_writes_values():
    r = FakeRedis()
    svc = BaseService(repo=object(), redis=r)

    await svc.set_cache_list("k", ["x", "y"])
    got = await svc.get_cached_list("k")
    assert sorted(got) == ["x", "y"]
