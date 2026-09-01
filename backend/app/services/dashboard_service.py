from datetime import datetime
from typing import Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.schemas.dashboard import DashboardResponse


def get_dashboard_data(
    db: Session,
    user_id: int,
) -> DashboardResponse:
    """
    Return dashboard statistics for the authenticated user.

    This service only reads application metadata/mapping
    information. It never reads customer/business records.
    """

    # These imports are kept inside the function so the service
    # remains compatible while the persistence models are added.
    from app.models.database_connection import DatabaseConnection
    from app.models.metadata_table import MetadataTable
    from app.models.business_mapping import BusinessMapping

    connected_databases = (
        db.query(func.count(DatabaseConnection.id))
        .filter(
            DatabaseConnection.user_id == user_id,
            DatabaseConnection.connected.is_(True),
        )
        .scalar()
        or 0
    )

    total_tables = (
        db.query(func.count(MetadataTable.id))
        .filter(
            MetadataTable.user_id == user_id,
        )
        .scalar()
        or 0
    )

    total_mapped_tables = (
        db.query(func.count(BusinessMapping.id))
        .filter(
            BusinessMapping.user_id == user_id,
        )
        .scalar()
        or 0
    )

    last_mapping = (
        db.query(BusinessMapping.created_at)
        .filter(
            BusinessMapping.user_id == user_id,
        )
        .order_by(
            BusinessMapping.created_at.desc()
        )
        .first()
    )

    last_mapping_date: Optional[str] = None

    if last_mapping and last_mapping[0]:
        value = last_mapping[0]

        if isinstance(value, datetime):
            last_mapping_date = value.isoformat()
        else:
            last_mapping_date = str(value)

    return DashboardResponse(
        connected_databases=connected_databases,
        last_mapping_date=last_mapping_date,
        total_tables=total_tables,
        total_mapped_tables=total_mapped_tables,
    )