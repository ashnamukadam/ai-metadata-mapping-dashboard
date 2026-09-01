from datetime import datetime, UTC

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.database.base import Base


class MetadataTable(Base):
    __tablename__ = "metadata_tables"

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

    table_type = Column(
        String(50),
        nullable=False,
        default="table",
    )

    created_at = Column(
        DateTime,
        default=lambda: datetime.now(UTC),
        nullable=False,
    )

    user = relationship(
        "User",
    )

    database_connection = relationship(
        "DatabaseConnection",
    )