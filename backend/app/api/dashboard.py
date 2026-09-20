from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy import distinct, func
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.database.session import get_db

from app.models.database_connection import DatabaseConnection
from app.models.metadata_table import MetadataTable
from app.models.metadata_column import MetadataColumn
from app.models.relationship import Relationship
from app.models.business_mapping import BusinessMapping


router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard"],
)


@router.get("/stats")
def get_dashboard_stats(
    current_user: Any = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    # =========================================================
    # DATABASE COUNT
    # =========================================================

    databases = (
        db.query(DatabaseConnection)
        .filter(
            DatabaseConnection.user_id == current_user.id
        )
        .count()
    )

    # =========================================================
    # SCHEMA COUNT
    # =========================================================

    schemas = (
        db.query(
            func.count(
                distinct(MetadataTable.schema_name)
            )
        )
        .filter(
            MetadataTable.user_id == current_user.id,
            MetadataTable.schema_name.isnot(None),
        )
        .scalar()
        or 0
    )

    # =========================================================
    # TABLE COUNT
    # =========================================================

    tables = (
        db.query(MetadataTable)
        .filter(
            MetadataTable.user_id == current_user.id,
            func.upper(
                MetadataTable.table_type
            ).notin_(
                ["VIEW"]
            ),
        )
        .count()
    )

    # =========================================================
    # COLUMN COUNT
    # =========================================================

    columns = (
        db.query(MetadataColumn)
        .filter(
            MetadataColumn.user_id == current_user.id
        )
        .count()
    )

    # =========================================================
    # VIEW COUNT
    # =========================================================

    views = (
        db.query(MetadataTable)
        .filter(
            MetadataTable.user_id == current_user.id,
            func.upper(
                MetadataTable.table_type
            ) == "VIEW",
        )
        .count()
    )

    # =========================================================
    # RELATIONSHIP COUNT
    # =========================================================

    relationships = (
        db.query(Relationship)
        .filter(
            Relationship.user_id == current_user.id
        )
        .count()
    )

    # =========================================================
    # MAPPED TABLE COUNT
    #
    # Count unique tables for which the user has created
    # a business mapping.
    # =========================================================

    mapped_tables = (
        db.query(
            func.count(
                distinct(BusinessMapping.table_name)
            )
        )
        .filter(
            BusinessMapping.user_id == current_user.id
        )
        .scalar()
        or 0
    )

    # =========================================================
    # LAST MAPPING DATE
    #
    # updated_at is used so editing an existing mapping
    # updates the "Last Mapping Date".
    # =========================================================

    last_mapping_date = (
        db.query(
            func.max(
                BusinessMapping.updated_at
            )
        )
        .filter(
            BusinessMapping.user_id == current_user.id
        )
        .scalar()
    )

    # Convert datetime to ISO string for frontend
    if last_mapping_date:
        last_mapping_date = (
            last_mapping_date.isoformat()
        )

    # =========================================================
    # RESPONSE
    # =========================================================

    return {
        "databases": databases,
        "schemas": schemas,
        "tables": tables,
        "mapped_tables": mapped_tables,
        "columns": columns,
        "views": views,
        "relationships": relationships,
        "last_mapping_date": last_mapping_date,
    }