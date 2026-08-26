from typing import Any, Dict

from app.schemas.relationship import RelationshipRequest


def create_relationship(
    request: RelationshipRequest,
    schema_metadata: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Validate and create a relationship between two database columns.

    The relationship is created only against schema metadata.
    No business records are accessed or stored.
    """

    database_name = request.database_name

    # --------------------------------------------------------
    # DATABASE VALIDATION
    # --------------------------------------------------------

    if schema_metadata.get("database_name") != database_name:
        raise ValueError(
            "Database name does not match the supplied schema metadata."
        )

    # --------------------------------------------------------
    # TABLE LOOKUP
    # --------------------------------------------------------

    tables = schema_metadata.get("tables", [])

    parent_table = None
    child_table = None

    for table in tables:
        table_name = table.get("name")

        if table_name == request.parent_table:
            parent_table = table

        if table_name == request.child_table:
            child_table = table

    if parent_table is None:
        raise ValueError(
            f"Parent table '{request.parent_table}' "
            "was not found in schema metadata."
        )

    if child_table is None:
        raise ValueError(
            f"Child table '{request.child_table}' "
            "was not found in schema metadata."
        )

    # --------------------------------------------------------
    # COLUMN LOOKUP
    # --------------------------------------------------------

    parent_columns = {
        column.get("name")
        for column in parent_table.get("columns", [])
        if column.get("name")
    }

    child_columns = {
        column.get("name")
        for column in child_table.get("columns", [])
        if column.get("name")
    }

    if request.parent_column not in parent_columns:
        raise ValueError(
            f"Parent column '{request.parent_column}' "
            f"does not exist in table '{request.parent_table}'."
        )

    if request.child_column not in child_columns:
        raise ValueError(
            f"Child column '{request.child_column}' "
            f"does not exist in table '{request.child_table}'."
        )

    # --------------------------------------------------------
    # RELATIONSHIP
    # --------------------------------------------------------

    relationship = {
        "database_name": database_name,
        "parent_table": request.parent_table,
        "parent_column": request.parent_column,
        "child_table": request.child_table,
        "child_column": request.child_column,
    }

    return relationship