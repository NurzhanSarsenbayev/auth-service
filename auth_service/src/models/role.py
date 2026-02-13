import uuid
from datetime import datetime

from db.postgres import Base
from sqlalchemy import Column, DateTime, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship


class Role(Base):
    __tablename__ = "roles"
    __table_args__ = {"extend_existing": True}

    role_id = Column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False
    )
    name = Column(String(50), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user_roles = relationship(
        "UserRole", back_populates="role", cascade="all, delete-orphan", lazy="selectin"
    )
