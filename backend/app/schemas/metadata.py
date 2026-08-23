from typing import Any

from pydantic import BaseModel, Field


class ColumnMetadataResponse(BaseModel):
    name: str
    data_type: str
    nullable: bool
    primary_key: bool = False
    auto_increment: bool = False
    default: Any = None
    constraints: list[str] = Field(default_factory=list)


class IndexMetadataResponse(BaseModel):
    name: str
    columns: list[str] = Field(default_factory=list)
    unique: bool = False


class ForeignKeyMetadataResponse(BaseModel):
    column: str
    referenced_table: str
    referenced_column: str
    constraint_name: str | None = None


class TableMetadataResponse(BaseModel):
    name: str
    table_type: str

    columns: list[ColumnMetadataResponse] = Field(
        default_factory=list
    )

    primary_keys: list[str] = Field(
        default_factory=list
    )

    foreign_keys: list[ForeignKeyMetadataResponse] = Field(
        default_factory=list
    )

    indexes: list[IndexMetadataResponse] = Field(
        default_factory=list
    )

    constraints: list[str] = Field(
        default_factory=list
    )


class DatabaseMetadataResponse(BaseModel):
    database_name: str
    database_type: str

    tables: list[TableMetadataResponse] = Field(
        default_factory=list
    )

    views: list[TableMetadataResponse] = Field(
        default_factory=list
    )


class MetadataExtractionResponse(BaseModel):
    message: str
    metadata: DatabaseMetadataResponse
    metadata_only: bool = True