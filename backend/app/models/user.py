from datetime import datetime, UTC

from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship

from app.database.base import Base


class User(Base):
    __tablename__ = "users"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    name = Column(
        String(100),
        nullable=False,
    )

    email = Column(
        String(100),
        unique=True,
        nullable=False,
    )

    password_hash = Column(
        String(255),
        nullable=False,
    )

    created_at = Column(
        DateTime,
        default=lambda: datetime.now(UTC),
    )

    database_connections = relationship(
        "DatabaseConnection",
        back_populates="user",
        cascade="all, delete-orphan",
    )