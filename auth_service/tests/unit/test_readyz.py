import asyncio
from contextlib import asynccontextmanager

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.v1.ready import router as ready_router


class DummySession:
    async def execute(self, *_args, **_kwargs):
        return 1


@asynccontextmanager
async def ok_session_factory():
    yield DummySession()


@asynccontextmanager
async def fail_session_factory():
    raise RuntimeError("db down")
    yield  # pragma: no cover


class DummyRedisPool:
    connection_kwargs = {"host": "redis", "port": 6379}


class DummyRedis:
    connection_pool = DummyRedisPool()


@pytest.fixture
def app():
    app = FastAPI()
    app.include_router(ready_router, prefix="/api/v1")
    return app


def test_readyz_ok(monkeypatch, app):
    # Arrange
    app.state.session_factory = ok_session_factory
    app.state.redis = DummyRedis()

    # Make redis TCP check succeed fast
    monkeypatch.setattr(asyncio, "to_thread", lambda *args, **kwargs: asyncio.sleep(0))

    client = TestClient(app)

    # Act
    r = client.get("/api/v1/readyz")

    # Assert
    assert r.status_code == 200
    assert r.json()["status"] == "ready"
    assert r.json()["details"]["postgres"] == "ok"
    assert r.json()["details"]["redis"] == "ok"


def test_readyz_postgres_error(monkeypatch, app):
    app.state.session_factory = fail_session_factory
    app.state.redis = DummyRedis()

    monkeypatch.setattr(asyncio, "to_thread", lambda *args, **kwargs: asyncio.sleep(0))

    client = TestClient(app)
    r = client.get("/api/v1/readyz")

    assert r.status_code == 503
    body = r.json()
    assert body["status"] == "not_ready"
    assert body["details"]["postgres"] == "error"
    assert body["details"]["redis"] == "ok"


def test_readyz_redis_timeout(monkeypatch, app):
    app.state.session_factory = ok_session_factory
    app.state.redis = DummyRedis()

    async def raise_timeout(*_a, **_kw):
        raise TimeoutError()

    monkeypatch.setattr(asyncio, "to_thread", raise_timeout)

    client = TestClient(app)
    r = client.get("/api/v1/readyz")

    assert r.status_code == 503
    assert r.json()["details"]["redis"] == "error"


def test_readyz_redis_dns_error(monkeypatch, app):
    app.state.session_factory = ok_session_factory
    app.state.redis = DummyRedis()

    async def raise_oserror(*_a, **_kw):
        raise OSError("No address associated with hostname")

    monkeypatch.setattr(asyncio, "to_thread", raise_oserror)

    client = TestClient(app)
    r = client.get("/api/v1/readyz")

    assert r.status_code == 503
    assert r.json()["details"]["redis"] == "error"
