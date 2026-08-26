import json
from typing import Any, Dict

from app.schemas.export_mapping import ExportMappingRequest


def generate_mapping_json(
    request: ExportMappingRequest,
) -> str:
    """
    Generate the mapping.json representation.

    No database records are accessed.
    No credentials are included.
    """

    entities = []

    for entity in request.entities:
        entity_data: Dict[str, Any] = {
            "entity": entity.entity,
            "table": entity.table,
            "aliases": entity.aliases,
            "primaryKey": entity.primary_key,
            "fields": entity.fields,
        }

        if entity.description is not None:
            entity_data["description"] = entity.description

        if entity.status_field is not None:
            entity_data["statusField"] = entity.status_field

        entities.append(entity_data)

    result: Dict[str, Any] = {
        "database": request.database,
        "entities": entities,
    }

    if request.relationships:
        result["relationships"] = [
            {
                "parentTable": relationship.parent_table,
                "parentColumn": relationship.parent_column,
                "childTable": relationship.child_table,
                "childColumn": relationship.child_column,
            }
            for relationship in request.relationships
        ]

    return json.dumps(
        result,
        indent=2,
    )


def generate_mapping_txt(
    request: ExportMappingRequest,
) -> str:
    """
    Generate the human-readable mapping.txt representation.

    No database records are accessed.
    No credentials are included.
    """

    lines = []

    for entity in request.entities:
        lines.extend(
            [
                "DATABASE",
                "",
                request.database,
                "",
                "ENTITY",
                "",
                entity.entity,
                "",
                "TABLE",
                "",
                entity.table,
                "",
            ]
        )

        if entity.description is not None:
            lines.extend(
                [
                    "DESCRIPTION",
                    "",
                    entity.description,
                    "",
                ]
            )

        lines.append("ALIASES")
        lines.append("")

        for alias in entity.aliases:
            lines.append(alias)

        lines.extend(
            [
                "",
                "PRIMARY KEY",
                "",
                entity.primary_key or "",
                "",
                "FIELDS",
                "",
            ]
        )

        for column_name, business_name in entity.fields.items():
            lines.append(
                f"{column_name} -> {business_name}"
            )

        if entity.status_field is not None:
            lines.extend(
                [
                    "",
                    "STATUS FIELD",
                    "",
                    entity.status_field,
                    "",
                ]
            )

    if request.relationships:
        lines.extend(
            [
                "RELATIONSHIPS",
                "",
            ]
        )

        for relationship in request.relationships:
            lines.append(
                f"{relationship.parent_table}."
                f"{relationship.parent_column}"
                " -> "
                f"{relationship.child_table}."
                f"{relationship.child_column}"
            )

    return "\n".join(lines)