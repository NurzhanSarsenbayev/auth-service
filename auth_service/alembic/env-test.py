import os
from alembic import context
from sqlalchemy import engine_from_config, pool

from core.models import Base


config = context.config
target_metadata = Base.metadata


def _build_db_url() -> str:
    # 1) explicit URL
    db_url = os.getenv("DB_URL")
    if db_url:
        return db_url

    # 2) from parts
    host = os.getenv("DB_HOST", "localhost")
    port = os.getenv("DB_PORT", "5432")
    name = os.getenv("DB_NAME", "postgres")
    user = os.getenv("DB_USER", "postgres")
    password = os.getenv("DB_PASSWORD", "postgres")
    return f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{name}"


def _alembic_sync_url(async_url: str) -> str:
    # Alembic needs sync driver
    return async_url.replace("postgresql+asyncpg://", "postgresql://")


def run_migrations_offline() -> None:
    url = _alembic_sync_url(_build_db_url())
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True)

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    url = _alembic_sync_url(_build_db_url())
    config.set_main_option("sqlalchemy.url", url)

    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
