from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.models.business_mapping import BusinessMapping
from app.models.column_mapping import ColumnMapping
from app.models.database_connection import DatabaseConnection
from app.models.relationship import Relationship
from app.schemas.ai_prompt_preview import AIPromptPreviewRequest


def generate_ai_prompt_preview(
    request: AIPromptPreviewRequest,
    db: Optional[Session] = None,
    user_id: Optional[int] = None,
) -> str:
    """
    Generate a deterministic AI prompt preview.

    No AI model is used.
    No database business records are accessed.

    When db and user_id are supplied, the preview is generated
    from persisted business mappings, column mappings, and
    relationships belonging to the authenticated user.
    """

    table_name = request.table_name

    important_fields: List[str] = [
        field.strip()
        for field in request.important_fields
        if field and field.strip()
    ]

    relationships: List[Dict[str, Any]] = list(
        request.relationships
    )

    # --------------------------------------------------------
    # LOAD PERSISTED MAPPING DATA
    # --------------------------------------------------------

    if db is not None and user_id is not None:

        database_connection = (
            db.query(DatabaseConnection)
            .filter(
                DatabaseConnection.user_id == user_id,
                DatabaseConnection.database_name
                == request.database_name,
            )
            .order_by(
                DatabaseConnection.created_at.desc()
            )
            .first()
        )

        if database_connection is not None:

            business_mapping = (
                db.query(BusinessMapping)
                .filter(
                    BusinessMapping.user_id == user_id,
                    BusinessMapping.database_connection_id
                    == database_connection.id,
                    BusinessMapping.table_name == table_name,
                )
                .first()
            )

            # Add mapped business fields where available.
            if business_mapping is not None:
                for field in [
                    business_mapping.primary_identifier,
                    business_mapping.date_field,
                    business_mapping.amount_field,
                    business_mapping.status_field,
                    business_mapping.customer_reference,
                ]:
                    if field and field not in important_fields:
                        important_fields.append(field)

            # Add column business names as useful preview fields.
            column_mappings = (
                db.query(ColumnMapping)
                .filter(
                    ColumnMapping.user_id == user_id,
                    ColumnMapping.database_connection_id
                    == database_connection.id,
                    ColumnMapping.table_name == table_name,
                )
                .all()
            )

            for column in column_mappings:
                if column.column_name not in important_fields:
                    important_fields.append(
                        column.column_name
                    )

            persisted_relationships = (
                db.query(Relationship)
                .filter(
                    Relationship.user_id == user_id,
                    Relationship.database_connection_id
                    == database_connection.id,
                )
                .all()
            )

            relationships = [
                {
                    "parent_table": relationship.parent_table,
                    "parent_column": relationship.parent_column,
                    "child_table": relationship.child_table,
                    "child_column": relationship.child_column,
                }
                for relationship in persisted_relationships
            ]

    # --------------------------------------------------------
    # HEADER
    # --------------------------------------------------------

    preview_lines = [
        (
            f"{table_name} data can be found "
            f"inside table {table_name}."
        ),
        "",
        "Important fields:",
    ]

    # --------------------------------------------------------
    # IMPORTANT FIELDS
    # --------------------------------------------------------

    for field in important_fields:
        preview_lines.append(field)

    # --------------------------------------------------------
    # RELATIONSHIPS
    # --------------------------------------------------------

    relationship_lines = []

    for relationship in relationships:

        parent_table = relationship.get("parent_table")
        parent_column = relationship.get("parent_column")
        child_table = relationship.get("child_table")
        child_column = relationship.get("child_column")

        if not all(
            [
                parent_table,
                parent_column,
                child_table,
                child_column,
            ]
        ):
            continue

        if parent_table == table_name:
            relationship_lines.append(
                f"Join {child_table} using {parent_column}."
            )

        elif child_table == table_name:
            relationship_lines.append(
                f"Join {parent_table} using {child_column}."
            )

    if relationship_lines:
        preview_lines.append("")
        preview_lines.extend(relationship_lines)

    return "\n".join(preview_lines)