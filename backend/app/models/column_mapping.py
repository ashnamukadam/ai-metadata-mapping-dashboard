from datetime import datetime, UTC

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from app.database.base import Base


class ColumnMapping(Base):
    __tablename__ = "column_mappings"

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

    table_name = Column(
        String(255),
        nullable=False,
    )

    column_name = Column(
        String(255),
        nullable=False,
    )

    business_name = Column(
        String(255),
        nullable=False,
    )

    description = Column(
        Text,
        nullable=False,
    )

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

    user = relationship("User")
    database_connection = relationship("DatabaseConnection")