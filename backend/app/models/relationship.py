from datetime import datetime, UTC

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.orm import relationship

from app.database.base import Base


class Relationship(Base):
    __tablename__ = "relationships"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    database_connection_id = Column(
        Integer,
        ForeignKey(
            "database_connections.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    parent_table = Column(
        String(255),
        nullable=False,
    )

    parent_column = Column(
        String(255),
        nullable=False,
    )

    child_table = Column(
        String(255),
        nullable=False,
    )

    child_column = Column(
        String(255),
        nullable=False,
    )

    created_at = Column(
        DateTime,
        default=lambda: datetime.now(UTC),
        nullable=False,
    )

    user = relationship("User")
    database_connection = relationship("DatabaseConnection")