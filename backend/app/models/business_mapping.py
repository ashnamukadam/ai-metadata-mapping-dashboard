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


class BusinessMapping(Base):
    __tablename__ = "business_mappings"

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

    business_entity = Column(
        String(255),
        nullable=False,
    )

    table_purpose = Column(
        Text,
        nullable=False,
    )

    # Stored as JSON text so we don't need a database-specific
    # JSON column type.
    ai_aliases = Column(
        Text,
        nullable=False,
        default="[]",
    )

    primary_identifier = Column(
        String(255),
        nullable=True,
    )

    date_field = Column(
        String(255),
        nullable=True,
    )

    amount_field = Column(
        String(255),
        nullable=True,
    )

    status_field = Column(
        String(255),
        nullable=True,
    )

    customer_reference = Column(
        String(255),
        nullable=True,
    )

    description = Column(
        Text,
        nullable=True,
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

    user = relationship(
        "User",
    )

    database_connection = relationship(
        "DatabaseConnection",
    )