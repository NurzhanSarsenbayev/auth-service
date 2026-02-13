import os
import sys
from logging.config import fileConfig
from db.postgres import Base
from sqlalchemy import create_engine, pool
from alembic import context
from models.user import User
from models.role import Role
from models.user_role import UserRole
from models.login_history import LoginHistory
from models.social_account import SocialAccount

sys.path.append("src")

from core.config import Settings

settings = Settings()


config = context.config
fileConfig(config.config_file_name)

# Read DB URL from alembic.ini or environment.
url = (
    config.get_main_option("sqlalchemy.url")
    or os.getenv("DB_URL")
    or settings.database_url
)

# If URL is async (asyncpg), convert it to sync for Alembic.
url = url.replace("+asyncpg", "")

target_metadata = Base.metadata


def run_migrations_offline():
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    connectable = create_engine(url, poolclass=pool.NullPool)
    with connectable.connect() as connection:
        context.configure(connection=connection,
                          target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
