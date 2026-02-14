import uuid

from db.postgres import Base
from sqlalchemy import Boolean, Column, DateTime, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from utils.utc_now import utcnow


class User(Base):
    __tablename__ = "users"
    __table_args__ = {"extend_existing": True}

    user_id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        unique=True,
        nullable=False,
    )
    username = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=utcnow, nullable=False)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)

    user_roles = relationship(
        "UserRole",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    login_history = relationship("LoginHistory", back_populates="user")
    social_accounts = relationship("SocialAccount", back_populates="user", cascade="all, delete")

    @property
    def roles(self):
        return [ur.role for ur in self.user_roles if ur.role]
