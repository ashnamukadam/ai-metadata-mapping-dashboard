from datetime import datetime, UTC

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.database.base import Base


class DatabaseConnection(Base):
    __tablename__ = "database_connections"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    database_type = Column(String(50), nullable=False)
    database_name = Column(String(255), nullable=False)

    # Only connection metadata is stored.
    # NEVER store database passwords, secrets, or
    # credential-bearing connection strings here.
    connected = Column(Boolean, default=True, nullable=False)

    created_at = Column(
        DateTime,
        default=lambda: datetime.now(UTC),
        nullable=False,
    )

    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )

    user = relationship(
        "User",
        back_populates="database_connections",
    )