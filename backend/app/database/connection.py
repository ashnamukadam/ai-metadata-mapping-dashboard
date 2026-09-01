from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config.settings import DATABASE_URL
from app.database.base import Base

# Import all models so SQLAlchemy registers them before
# create_all() runs.
from app.models import (
    User,
    DatabaseConnection,
    MetadataTable,
    BusinessMapping,
)

engine = create_engine(
    DATABASE_URL
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

Base.metadata.create_all(
    bind=engine
)