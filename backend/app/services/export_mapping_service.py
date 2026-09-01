import json
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from app.models.business_mapping import BusinessMapping
from app.models.column_mapping import ColumnMapping
from app.models.database_connection import DatabaseConnection
from app.models.relationship import Relationship
from app.schemas.export_mapping import (
    ExportEntity,
    ExportMappingRequest,
    ExportRelationship,
)


def build_export_mapping(
    database: str,
    db: Session,
    user_id: int,
) -> ExportMappingRequest:
    """
    Build an exportable mapping from the authenticated user's
    persisted metadata mappings.

    Only metadata and mapping configuration are exported.
    No business/customer records or database credentials
    are accessed.
    """

    database_connection = (
        db.query(DatabaseConnection)
        .filter(
            DatabaseConnection.user_id == user_id,
            DatabaseConnection.database_name == database,
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

    business_mappings = (
        db.query(BusinessMapping)
        .filter(
            BusinessMapping.user_id == user_id,
            BusinessMapping.database_connection_id
            == database_connection.id,
        )
        .order_by(BusinessMapping.table_name)
        .all()
    )

    column_mappings = (
        db.query(ColumnMapping)
        .filter(
            ColumnMapping.user_id == user_id,
            ColumnMapping.database_connection_id
            == database_connection.id,
        )
        .order_by(
            ColumnMapping.table_name,
            ColumnMapping.column_name,
        )
        .all()
    )

    relationships = (
        db.query(Relationship)
        .filter(
            Relationship.user_id == user_id,
            Relationship.database_connection_id
            == database_connection.id,
        )
        .order_by(Relationship.parent_table)
        .all()
    )

    # Group column mappings by table.
    fields_by_table: Dict[str, Dict[str, str]] = {}

    for column in column_mappings:
        fields_by_table.setdefault(
            column.table_name,
            {},
        )[column.column_name] = column.business_name

    # Build entities.
    entities = []

    for mapping in business_mappings:

        aliases = []

        if mapping.ai_aliases:
            try:
                aliases = json.loads(
                    mapping.ai_aliases
                )
            except (TypeError, json.JSONDecodeError):
                aliases = []

        entity = ExportEntity(
            entity=mapping.business_entity,
            table=mapping.table_name,
            description=mapping.description,
            aliases=aliases,
            primary_key=mapping.primary_identifier,
            fields=fields_by_table.get(
                mapping.table_name,
                {},
            ),
            status_field=mapping.status_field,
        )

        entities.append(entity)

    export_relationships = [
        ExportRelationship(
            parent_table=relationship.parent_table,
            parent_column=relationship.parent_column,
            child_table=relationship.child_table,
            child_column=relationship.child_column,
        )
        for relationship in relationships
    ]

    return ExportMappingRequest(
        database=database,
        entities=entities,
        relationships=export_relationships,
        format="json",
    )


def generate_mapping_json(
    request: ExportMappingRequest,
) -> str:
    """
    Generate mapping.json.

    Only mapping configuration is exported.
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
    Generate human-readable mapping.txt.

    Only mapping configuration is exported.
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

        lines.extend(
            [
                "ALIASES",
                "",
            ]
        )

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