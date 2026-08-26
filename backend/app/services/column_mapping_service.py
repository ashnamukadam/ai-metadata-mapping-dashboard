from typing import Any, Dict

from app.schemas.column_mapping import ColumnMappingRequest


def create_column_mapping(
    request: ColumnMappingRequest,
    schema_metadata: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Validate and create a business mapping for one database column.

    Only schema metadata is used.
    No business records are accessed or stored.
    """

    database_name = request.database_name
    table_name = request.table_name
    column_name = request.column_name

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

    if column_name not in columns:
        raise ValueError(
            f"Column '{column_name}' was not found "
            f"in table '{table_name}'."
        )

    # --------------------------------------------------------
    # BUSINESS MAPPING
    # --------------------------------------------------------

    return {
        "database_name": database_name,
        "table_name": table_name,
        "column_name": column_name,
        "business_name": request.business_name.strip(),
        "description": request.description.strip(),
    }