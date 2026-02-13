import asyncio
import os
import pytest
import pytest_asyncio
from helpers.superuser import ensure_superuser
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from main import app
from db.postgres import make_engine, make_session_factory, Base, get_session
from db.redis_db import init_redis, close_redis, get_redis
from core.config import settings
from models import User
from utils.security import hash_password


# ============================================================
#  EVENT LOOP
# ============================================================

@pytest.fixture(scope="session")
def event_loop():
    """A shared event loop for all tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# ============================================================
#  DATABASE
# ============================================================

@pytest_asyncio.fixture(scope="session")
async def engine():
    """Create a DB engine and schema for tests."""
    eng = make_engine(settings.database_url)
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield eng
    await eng.dispose()


@pytest_asyncio.fixture(scope="function")
async def db_session(engine):
    """Provide a DB session per test."""
    session_factory = make_session_factory(engine)
    async with session_factory() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture(autouse=True)
async def clean_db(engine):
    async with engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            await conn.execute(
                text(f'TRUNCATE "{table.name}" RESTART IDENTITY CASCADE'))

    ensure_superuser(
        settings.database_url.replace("+asyncpg", ""),
        password=os.getenv("SUPERUSER_PASSWORD", "123"),
    )
    yield

# ============================================================
#  REDIS
# ============================================================


@pytest_asyncio.fixture(scope="session")
async def redis_client():
    client = await init_redis()
    yield client
    await client.flushdb()
    await close_redis(client)


# ============================================================
#  DEPENDENCY OVERRIDES
# ============================================================

@pytest_asyncio.fixture(autouse=True)
def override_get_session(db_session: AsyncSession):
    async def _override():
        yield db_session
    app.dependency_overrides[get_session] = _override


@pytest_asyncio.fixture(autouse=True)
def override_get_redis(redis_client):
    async def _override():
        yield redis_client
    app.dependency_overrides[get_redis] = _override


# ============================================================
#  TEST CLIENT
# ============================================================

@pytest_asyncio.fixture(scope="function")
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


# ============================================================
#  HELPERS
# ============================================================

@pytest_asyncio.fixture
def create_user(db_session: AsyncSession):
    async def _create_user(username: str, email: str, password: str):
        user = User(
            username=username,
            email=email,
            hashed_password=hash_password(password),
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        return user

    return _create_user
