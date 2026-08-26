from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, Field


class ExportEntity(BaseModel):
    entity: str = Field(..., min_length=1)
    table: str = Field(..., min_length=1)

    description: Optional[str] = None

    aliases: List[str] = Field(
        default_factory=list
    )

    primary_key: Optional[str] = None

    fields: Dict[str, str] = Field(
        default_factory=dict
    )

    status_field: Optional[str] = None


class ExportRelationship(BaseModel):
    parent_table: str = Field(..., min_length=1)
    parent_column: str = Field(..., min_length=1)

    child_table: str = Field(..., min_length=1)
    child_column: str = Field(..., min_length=1)


class ExportMappingRequest(BaseModel):
    database: str = Field(..., min_length=1)

    entities: List[ExportEntity] = Field(
        default_factory=list
    )

    relationships: List[ExportRelationship] = Field(
        default_factory=list
    )

    format: Literal["txt", "json"] = "json"