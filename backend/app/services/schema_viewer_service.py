from typing import Any, Dict, List


def build_schema_view(metadata: Dict[str, Any]) -> Dict[str, Any]:
    """
    Build a simplified schema hierarchy for the Schema Viewer.

    Structure:
        Database
            └── Tables
                    └── Columns

    Only schema metadata is returned.
    Business records are never included.
    """

    database_name = metadata.get("database_name", "N/A")

    tables: List[Dict[str, Any]] = []

    for table in metadata.get("tables", []):
        columns: List[str] = []

        for column in table.get("columns", []):
            column_name = column.get("name")

            if column_name:
                columns.append(column_name)

        tables.append(
            {
                "name": table.get("name", "N/A"),
                "columns": columns,
            }
        )

    return {
        "database": database_name,
        "tables": tables,
    }