from typing import Dict, List, Optional

from pydantic import BaseModel, Field


# ============================================================
# EXPORT ENTITY
# ============================================================

class ExportEntity(BaseModel):
    entity: str = Field(
        ...,
        min_length=1,
        description="Business entity name.",
    )

    table: str = Field(
        ...,
        min_length=1,
        description="Database table associated with the entity.",
    )

    description: Optional[str] = Field(
        default=None,
        description="Description of the business entity.",
    )

    aliases: List[str] = Field(
        default_factory=list,
        description="Alternative names for the entity.",
    )

    primary_key: Optional[str] = Field(
        default=None,
        description="Primary business identifier.",
    )

    fields: Dict[str, str] = Field(
        default_factory=dict,
        description="Database column to business-name mappings.",
    )

    status_field: Optional[str] = Field(
        default=None,
        description="Column containing the business status.",
    )


# ============================================================
# EXPORT RELATIONSHIP
# ============================================================

class ExportRelationship(BaseModel):
    parent_table: str = Field(
        ...,
        min_length=1,
        description="Parent table name.",
    )

    parent_column: str = Field(
        ...,
        min_length=1,
        description="Parent table column.",
    )

    child_table: str = Field(
        ...,
        min_length=1,
        description="Child table name.",
    )

    child_column: str = Field(
        ...,
        min_length=1,
        description="Child table column.",
    )


# ============================================================
# EXPORT MAPPING REQUEST
# ============================================================

class ExportMappingRequest(BaseModel):
    database: str = Field(
        ...,
        min_length=1,
        description="Database name.",
    )

    entities: List[ExportEntity] = Field(
        default_factory=list,
        description="Business entities included in the mapping.",
    )

    relationships: List[ExportRelationship] = Field(
        default_factory=list,
        description="Database relationships included in the mapping.",
    )

    format: str = Field(
        default="json",
        description="Export format.",
    )