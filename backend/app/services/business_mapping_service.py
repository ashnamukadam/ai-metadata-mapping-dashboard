import json
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from app.models.business_mapping import BusinessMapping
from app.models.database_connection import DatabaseConnection
from app.schemas.business_mapping import BusinessMappingRequest


def create_business_mapping(
    request: BusinessMappingRequest,
    schema_metadata: Dict[str, Any],
    db: Optional[Session] = None,
    user_id: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Validate and create a business mapping for a database table.

    The mapping is created only against schema metadata.
    No business records are accessed or stored.

    When db and user_id are supplied, the validated mapping is
    also persisted in the application's metadata database.
    """

    database_name = request.database_name
    table_name = request.table_name

    # --------------------------------------------------------
    # DATABASE VALIDATION
    # --------------------------------------------------------

    if schema_metadata.get("database_name") != database_name:
        raise ValueError(
            "Database name does not match the supplied schema metadata."
        )

    # --------------------------------------------------------
    # TABLE VALIDATION
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # COLUMN VALIDATION
    # --------------------------------------------------------

    columns = {
        column.get("name")
        for column in target_table.get("columns", [])
        if column.get("name")
    }

    selected_fields = {
        "primary_identifier": request.primary_identifier,
        "date_field": request.date_field,
        "amount_field": request.amount_field,
        "status_field": request.status_field,
        "customer_reference": request.customer_reference,
    }

    for field_name, column_name in selected_fields.items():
        if column_name is not None and column_name not in columns:
            raise ValueError(
                f"{field_name} '{column_name}' does not exist "
                f"in table '{table_name}'."
            )

    # --------------------------------------------------------
    # ALIAS CLEANING
    # --------------------------------------------------------

    aliases = [
        alias.strip()
        for alias in request.ai_aliases
        if alias and alias.strip()
    ]

    # --------------------------------------------------------
    # FINAL BUSINESS MAPPING
    # --------------------------------------------------------

    mapping = {
        "database_name": database_name,
        "business_entity": request.business_entity,
        "table": table_name,
        "table_name": table_name,
        "table_purpose": request.table_purpose,
        "aliases": aliases,
        "primary_identifier": request.primary_identifier,
        "date_field": request.date_field,
        "amount_field": request.amount_field,
        "status_field": request.status_field,
        "customer_reference": request.customer_reference,
        "description": request.description,
    }

    # --------------------------------------------------------
    # OPTIONAL PERSISTENCE
    # --------------------------------------------------------
    #
    # Existing callers/tests can continue calling the service
    # without db/user_id.
    #
    # When called by the authenticated API with db + user_id,
    # the mapping is stored in OUR application database only.
    #
    # No customer/business records are stored.

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
            db.query(BusinessMapping)
            .filter(
                BusinessMapping.user_id == user_id,
                BusinessMapping.database_connection_id
                == database_connection.id,
                BusinessMapping.table_name == table_name,
            )
            .first()
        )

        if existing_mapping is None:
            existing_mapping = BusinessMapping(
                user_id=user_id,
                database_connection_id=database_connection.id,
                table_name=table_name,
            )

            db.add(existing_mapping)

        existing_mapping.business_entity = (
            request.business_entity
        )

        existing_mapping.table_purpose = (
            request.table_purpose
        )

        existing_mapping.ai_aliases = json.dumps(
            aliases
        )

        existing_mapping.primary_identifier = (
            request.primary_identifier
        )

        existing_mapping.date_field = (
            request.date_field
        )

        existing_mapping.amount_field = (
            request.amount_field
        )

        existing_mapping.status_field = (
            request.status_field
        )

        existing_mapping.customer_reference = (
            request.customer_reference
        )

        existing_mapping.description = (
            request.description
        )

        db.commit()
        db.refresh(existing_mapping)

    return mapping