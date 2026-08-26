from pydantic import BaseModel, Field


class RelationshipRequest(BaseModel):
    database_name: str = Field(min_length=1)
    parent_table: str = Field(min_length=1)
    parent_column: str = Field(min_length=1)
    child_table: str = Field(min_length=1)
    child_column: str = Field(min_length=1)


class RelationshipResponse(BaseModel):
    message: str
    relationship: dict