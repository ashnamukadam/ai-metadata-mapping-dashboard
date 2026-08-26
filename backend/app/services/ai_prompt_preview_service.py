from typing import Any, Dict

from app.schemas.ai_prompt_preview import AIPromptPreviewRequest


def generate_ai_prompt_preview(
    request: AIPromptPreviewRequest,
) -> str:
    """
    Generate a deterministic AI prompt preview from
    business schema metadata.

    No AI model is used.
    No database records are accessed.
    """

    # --------------------------------------------------------
    # HEADER
    # --------------------------------------------------------

    preview_lines = [
        (
            f"{request.table_name} data can be found "
            f"inside table {request.table_name}."
        ),
        "",
        "Important fields:",
    ]

    # --------------------------------------------------------
    # IMPORTANT FIELDS
    # --------------------------------------------------------

    for field in request.important_fields:
        field = field.strip()

        if field:
            preview_lines.append(field)

    # --------------------------------------------------------
    # RELATIONSHIPS
    # --------------------------------------------------------

    if request.relationships:
        preview_lines.append("")
        
        for relationship in request.relationships:
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

            # For the selected table, describe the related
            # table using the relationship column.
            if parent_table == request.table_name:
                preview_lines.append(
                    f"Join {child_table} using {parent_column}."
                )

            elif child_table == request.table_name:
                preview_lines.append(
                    f"Join {parent_table} using {child_column}."
                )

    return "\n".join(preview_lines)