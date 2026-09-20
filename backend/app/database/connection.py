from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config.settings import DATABASE_URL
from app.database.base import Base

# ============================================================
# IMPORT ALL MODELS
# ============================================================

from app.models import (
    User,
    DatabaseConnection,
    MetadataTable,
    MetadataColumn,
    MetadataIndex,
    MetadataConstraint,
    BusinessMapping,
    ColumnMapping,
    Relationship,
)


# ============================================================
# DATABASE ENGINE
# ============================================================

engine = create_engine(
    DATABASE_URL
)


# ============================================================
# SESSION
# ============================================================

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


# ============================================================
# CREATE DATABASE TABLES
# ============================================================

Base.metadata.create_all(
    bind=engine
)