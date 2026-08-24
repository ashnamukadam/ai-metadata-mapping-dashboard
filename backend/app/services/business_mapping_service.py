from typing import Any, Dict

from app.schemas.business_mapping import BusinessMappingRequest


def create_business_mapping(
    request: BusinessMappingRequest,
    schema_metadata: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Validate and create a business mapping for a database table.

    The mapping is created only against schema metadata.
    No business records are accessed or stored.
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
        # Module 5 uses "name" for the table name.
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

    return mapping