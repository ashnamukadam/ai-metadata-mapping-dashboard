from typing import List, Literal, Optional

from pydantic import BaseModel, Field


class ColumnInfo(BaseModel):
    name: str = Field(..., min_length=1)
    data_type: Optional[str] = None
    nullable: Optional[bool] = None
    primary_key: Optional[bool] = None


class AIMappingRequest(BaseModel):
    database_name: str = Field(..., min_length=1)
    table_name: str = Field(..., min_length=1)

    mapping_type: Literal[
        "business_mapping",
        "column_mapping",
    ]

    columns: List[ColumnInfo] = Field(
        default_factory=list
    )

    relationships: List[dict] = Field(
        default_factory=list
    )


class BusinessMappingResult(BaseModel):
    business_entity: str
    table_purpose: str
    ai_aliases: List[str]
    primary_identifier: Optional[str] = None
    date_field: Optional[str] = None
    amount_field: Optional[str] = None
    status_field: Optional[str] = None
    customer_reference: Optional[str] = None
    description: str


class ColumnMappingResult(BaseModel):
    column_name: str
    business_name: str
    description: str
    business_category: str


class AIMappingResponse(BaseModel):
    message: str
    mapping_type: str
    table_name: str
    business_mapping: Optional[BusinessMappingResult] = None
    column_mappings: Optional[List[ColumnMappingResult]] = None