from typing import List, Literal

from pydantic import BaseModel, Field


class AIPromptPreviewRequest(BaseModel):
    database_name: str = Field(..., min_length=1)
    table_name: str = Field(..., min_length=1)

    prompt_type: Literal[
        "business_mapping",
        "column_mapping"
    ] = "business_mapping"

    important_fields: List[str] = Field(
        default_factory=list
    )

    relationships: List[dict] = Field(
        default_factory=list
    )


class AIPromptPreviewResponse(BaseModel):
    message: str
    preview: str