import json
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from app.models.column_mapping import ColumnMapping
from app.models.database_connection import DatabaseConnection
from app.schemas.column_mapping import ColumnMappingRequest


def create_column_mapping(
    request: ColumnMappingRequest,
    schema_metadata: Dict[str, Any],
    db: Optional[Session] = None,
    user_id: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Validate and create a business mapping for one database column.

    Only schema metadata is used.
    No business records are accessed or stored.

    When db and user_id are supplied, the validated mapping is
    persisted in the application's metadata database.
    """

    database_name = request.database_name
    table_name = request.table_name
    column_name = request.column_name

    if schema_metadata.get("database_name") != database_name:
        raise ValueError(
            "Database name does not match the supplied schema metadata."
        )

    tables = schema_metadata.get("tables", [])

    target_table = None

    for table in tables:
        if table.get("name") == table_name:
            target_table = table
            break

    if target_table is None:
        raise ValueError(
            f"Table '{table_name}' was not found in schema metadata."
        )

    columns = {
        column.get("name")
        for column in target_table.get("columns", [])
        if column.get("name")
    }

    if column_name not in columns:
        raise ValueError(
            f"Column '{column_name}' was not found "
            f"in table '{table_name}'."
        )

    business_name = request.business_name.strip()
    description = request.description.strip()

    mapping = {
        "database_name": database_name,
        "table_name": table_name,
        "column_name": column_name,
        "business_name": business_name,
        "description": description,
    }

    # --------------------------------------------------------
    # OPTIONAL PERSISTENCE
    # --------------------------------------------------------

    if db is not None and user_id is not None:

        database_connection = (
            db.query(DatabaseConnection)
            .filter(
                DatabaseConnection.user_id == user_id,
                DatabaseConnection.database_name == database_name,
            )
            .order_by(
                DatabaseConnection.created_at.desc()
            )
            .first()
        )

        if database_connection is None:
            raise ValueError(
                "Database connection was not found for this user."
            )

        existing_mapping = (
            db.query(ColumnMapping)
            .filter(
                ColumnMapping.user_id == user_id,
                ColumnMapping.database_connection_id
                == database_connection.id,
                ColumnMapping.table_name == table_name,
                ColumnMapping.column_name == column_name,
            )
            .first()
        )

        if existing_mapping is None:
            existing_mapping = ColumnMapping(
                user_id=user_id,
                database_connection_id=database_connection.id,
                table_name=table_name,
                column_name=column_name,
            )

            db.add(existing_mapping)

        existing_mapping.business_name = business_name
        existing_mapping.description = description

        db.commit()
        db.refresh(existing_mapping)

    return mapping