from typing import Optional

from pydantic import BaseModel, Field


class ColumnMappingRequest(BaseModel):
    database_name: str = Field(..., min_length=1)
    table_name: str = Field(..., min_length=1)
    column_name: str = Field(..., min_length=1)

    business_name: str = Field(..., min_length=1)
    description: str = Field(..., min_length=1)


class ColumnMappingResponse(BaseModel):
    message: str
    mapping: dict