from typing import List, Optional

from pydantic import BaseModel, Field


class BusinessMappingRequest(BaseModel):
    database_name: str = Field(
        ...,
        min_length=1,
        description="Name of the database being mapped.",
    )

    table_name: str = Field(
        ...,
        min_length=1,
        description="Name of the database table being mapped.",
    )

    business_entity: str = Field(
        ...,
        min_length=1,
        description="Business meaning/entity represented by the table.",
    )

    table_purpose: str = Field(
        ...,
        min_length=1,
        description="Purpose of the table in business terms.",
    )

    ai_aliases: List[str] = Field(
        default_factory=list,
        description="Alternative names the AI may use for this business entity.",
    )

    primary_identifier: Optional[str] = Field(
        default=None,
        description="Column selected as the primary business identifier.",
    )

    date_field: Optional[str] = Field(
        default=None,
        description="Column containing the relevant business date.",
    )

    amount_field: Optional[str] = Field(
        default=None,
        description="Column containing the relevant monetary amount.",
    )

    status_field: Optional[str] = Field(
        default=None,
        description="Column containing the business status.",
    )

    customer_reference: Optional[str] = Field(
        default=None,
        description="Column referencing the customer.",
    )

    description: Optional[str] = Field(
        default=None,
        description="Additional free-text description of the business mapping.",
    )


class BusinessMappingResponse(BaseModel):
    message: str
    mapping: BusinessMappingRequest