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


class MetadataColumn(Base):
    __tablename__ = "metadata_columns"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

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

    data_type = Column(
        String(255),
        nullable=False,
    )

    nullable = Column(
        Integer,
        nullable=False,
        default=1,
    )

    primary_key = Column(
        Integer,
        nullable=False,
        default=0,
    )

    auto_increment = Column(
        Integer,
        nullable=False,
        default=0,
    )

    created_at = Column(
        DateTime,
        default=lambda: datetime.now(UTC),
        nullable=False,
    )

    user = relationship("User")
    database_connection = relationship("DatabaseConnection")