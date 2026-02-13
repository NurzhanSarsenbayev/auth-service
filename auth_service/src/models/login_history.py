import uuid
from datetime import datetime

from db.postgres import Base
from sqlalchemy import Column, DateTime, ForeignKey, Index, String, desc
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship


class LoginHistory(Base):
    __tablename__ = "login_history"
    __table_args__ = (
        # не обязательно объявлять, индекс уже создан миграцией,
        # но так ORM «знает» о нём; в БД ничего не меняет
        Index("ix_login_history_user_id_time", "user_id", desc("login_time")),
        {"extend_existing": True},
    )

    # составной PK как в БД
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    login_time = Column(DateTime, primary_key=True, default=datetime.utcnow, nullable=False)

    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False,
    )
    user_agent = Column(String(255), nullable=True)
    ip_address = Column(String(50), nullable=True)

    user = relationship("User", back_populates="login_history")

    def __repr__(self) -> str:
        return (
            f"<LoginHistory id={self.id} user_id={self.user_id} at={self.login_time.isoformat()}>"
        )
