from typing import List

from sqlalchemy.orm import Session

from app.models.business_mapping import BusinessMapping
from app.models.column_mapping import ColumnMapping
from app.models.database_connection import DatabaseConnection
from app.models.relationship import Relationship
from app.schemas.ai_prompt_preview import AIPromptPreviewRequest


def generate_ai_prompt_preview(
    request: AIPromptPreviewRequest,
    db: Session | None = None,
    user_id: int | None = None,
) -> str:
    """
    Generate a deterministic AI prompt preview.

    Supports:
    - business_mapping
    - column_mapping

    No AI model is used.
    """

    if request.prompt_type == "column_mapping":
        return generate_column_mapping_prompt(request)

    return generate_business_mapping_prompt(
        request=request,
        db=db,
        user_id=user_id,
    )


# ============================================================
# BUSINESS MAPPING PROMPT
# ============================================================

def generate_business_mapping_prompt(
    request: AIPromptPreviewRequest,
    db: Session | None = None,
    user_id: int | None = None,
) -> str:

    table_name = request.table_name

    important_fields: List[str] = [
        field.strip()
        for field in request.important_fields
        if field and field.strip()
    ]

    relationships = list(
        request.relationships
    )

    # --------------------------------------------------------
    # LOAD SAVED BUSINESS MAPPING
    # --------------------------------------------------------

    business_mapping = None

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
                    BusinessMapping.table_name
                    == table_name,
                )
                .first()
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
                    "parent_table":
                        relationship.parent_table,

                    "parent_column":
                        relationship.parent_column,

                    "child_table":
                        relationship.child_table,

                    "child_column":
                        relationship.child_column,
                }
                for relationship in persisted_relationships
            ]

    # --------------------------------------------------------
    # BUILD BUSINESS MAPPING PROMPT
    # --------------------------------------------------------

    prompt_lines = [
        "You are an AI database metadata mapping assistant.",
        "",
        (
            "Analyze the following database table and "
            "determine its business meaning."
        ),
        "",
        "Database:",
        request.database_name,
        "",
        "Table:",
        table_name,
        "",
        "Important Fields:",
    ]

    if important_fields:
        for field in important_fields:
            prompt_lines.append(
                f"- {field}"
            )
    else:
        prompt_lines.append(
            "- No important fields specified."
        )

    # --------------------------------------------------------
    # SAVED BUSINESS INFORMATION
    # --------------------------------------------------------

    if business_mapping is not None:

        prompt_lines.extend(
            [
                "",
                "Existing Business Mapping:",
                "",
                f"Business Entity: "
                f"{business_mapping.business_entity}",

                f"Table Purpose: "
                f"{business_mapping.table_purpose}",

                f"AI Aliases: "
                f"{business_mapping.ai_aliases}",

                f"Primary Identifier: "
                f"{business_mapping.primary_identifier or 'Not specified'}",

                f"Date Field: "
                f"{business_mapping.date_field or 'Not specified'}",

                f"Amount Field: "
                f"{business_mapping.amount_field or 'Not specified'}",

                f"Status Field: "
                f"{business_mapping.status_field or 'Not specified'}",

                f"Customer Reference: "
                f"{business_mapping.customer_reference or 'Not specified'}",

                f"Description: "
                f"{business_mapping.description or 'Not specified'}",
            ]
        )

    # --------------------------------------------------------
    # RELATIONSHIPS
    # --------------------------------------------------------

    table_relationships = []

    for relationship in relationships:

        parent_table = relationship.get(
            "parent_table"
        )

        parent_column = relationship.get(
            "parent_column"
        )

        child_table = relationship.get(
            "child_table"
        )

        child_column = relationship.get(
            "child_column"
        )

        if not all(
            [
                parent_table,
                parent_column,
                child_table,
                child_column,
            ]
        ):
            continue

        if (
            parent_table == table_name
            or child_table == table_name
        ):
            table_relationships.append(
                (
                    f"{parent_table}."
                    f"{parent_column} → "
                    f"{child_table}."
                    f"{child_column}"
                )
            )

    if table_relationships:

        prompt_lines.extend(
            [
                "",
                "Relationships:",
            ]
        )

        for relationship in table_relationships:
            prompt_lines.append(
                f"- {relationship}"
            )

    # --------------------------------------------------------
    # REQUIRED OUTPUT
    # --------------------------------------------------------

    prompt_lines.extend(
        [
            "",
            "Generate the following business mapping:",
            "",
            "1. Business Entity",
            "2. Table Purpose",
            "3. Business Aliases",
            "4. Primary Identifier",
            "5. Date Field",
            "6. Amount Field",
            "7. Status Field",
            "8. Customer Reference",
            "9. Description",
            "",
            "Rules:",
            "- Use the table structure and field names "
              "to infer business meaning.",
            "- Do not invent unsupported information.",
            "- Keep business names clear and understandable "
              "to non-technical users.",
            "- If a field is not applicable, return "
              "'Not applicable'.",
            "- Keep the output concise and professional.",
        ]
    )

    return "\n".join(prompt_lines)


# ============================================================
# COLUMN MAPPING PROMPT
# ============================================================

def generate_column_mapping_prompt(
    request: AIPromptPreviewRequest,
) -> str:

    table_name = request.table_name

    important_fields = [
        field.strip()
        for field in request.important_fields
        if field and field.strip()
    ]

    prompt_lines = [
        "You are an AI database metadata mapping assistant.",
        "",
        (
            "Analyze the columns of the following database "
            "table and generate business-friendly column mappings."
        ),
        "",
        "Database:",
        request.database_name,
        "",
        "Table:",
        table_name,
        "",
        "Columns to Analyze:",
    ]

    if important_fields:

        for field in important_fields:
            prompt_lines.append(
                f"- {field}"
            )

    else:

        prompt_lines.append(
            "- No columns specified."
        )

    prompt_lines.extend(
        [
            "",
            "For each column, generate:",
            "",
            "1. Original Column Name",
            "2. Business Name",
            "3. Business Description",
            "4. Business Category",
            "",
            "Rules:",
            "- Keep the original column name unchanged.",
            "- Business Name must be easy for "
              "non-technical users to understand.",
            "- Business Description must clearly explain "
              "what information the column represents.",
            "- Do not invent information that cannot be "
              "reasonably inferred from the column name.",
            "- Use the table context when determining "
              "the business meaning.",
            "- Keep descriptions concise and professional.",
            "- If the meaning is uncertain, clearly state "
              "that it is inferred.",
            "",
            "Return the result in a structured format.",
        ]
    )

    return "\n".join(prompt_lines)