import os
import uuid
from datetime import datetime

from models import Role, User, UserRole
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from utils.security import hash_password


def ensure_superuser(db_url: str, password: str | None = None) -> None:
    """Create admin user + admin role if missing.

    Password priority:
      1) explicit `password` arg
      2) SUPERUSER_PASSWORD env var
    """
    password = password or os.getenv("SUPERUSER_PASSWORD")
    if not password:
        print("SUPERUSER_PASSWORD is not set -> skipping superuser creation")
        return

    engine = create_engine(db_url, echo=False, future=True)
    Session = sessionmaker(bind=engine)

    with Session() as session:
        user = session.execute(
            select(User).where(User.email == "admin@example.com")
        ).scalar_one_or_none()

        hashed = hash_password(password)

        if not user:
            user = User(
                user_id=uuid.uuid4(),
                username="admin",
                email="admin@example.com",
                hashed_password=hashed,
                is_active=True,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            session.add(user)
            session.flush()

        role = session.execute(select(Role).where(Role.name == "admin")).scalar_one_or_none()

        if not role:
            role = Role(
                role_id=uuid.uuid4(),
                name="admin",
                description="Administrator role",
                created_at=datetime.utcnow(),
            )
            session.add(role)
            session.flush()

        user_role = session.execute(
            select(UserRole).where(
                UserRole.user_id == user.user_id,
                UserRole.role_id == role.role_id,
            )
        ).scalar_one_or_none()

        if not user_role:
            session.add(
                UserRole(
                    id=uuid.uuid4(),
                    user_id=user.user_id,
                    role_id=role.role_id,
                    assigned_at=datetime.utcnow(),
                )
            )

        session.commit()
        print("✅ Superuser ensured")
