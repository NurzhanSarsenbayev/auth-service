from collections.abc import AsyncGenerator
from typing import Any

from core.config import settings
from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()


def make_engine(db_url: str | None = None, echo: bool = False):
    dsn = db_url or settings.database_url
    return create_async_engine(
        dsn,
        echo=echo,
        future=True,
        connect_args={"timeout": settings.db_connect_timeout_sec},
    )


def make_session_factory(engine):
    return sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)


async def get_session(request: Request) -> AsyncGenerator[AsyncSession, None]:
    session_factory: Any = request.app.state.session_factory
    async with session_factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
