from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.auth.dependencies import get_current_user
from app.schemas.relationship import (
    RelationshipRequest,
    RelationshipResponse,
)
from app.services.relationship_service import (
    create_relationship,
)


class RelationshipWithMetadataRequest(BaseModel):
    relationship: RelationshipRequest
    schema_metadata: dict[str, Any]


router = APIRouter(
    prefix="/database",
    tags=["Relationships"],
)


@router.post(
    "/relationship",
    response_model=RelationshipResponse,
    status_code=status.HTTP_200_OK,
)
def create_relationship_mapping(
    request: RelationshipWithMetadataRequest,
    current_user: Any = Depends(get_current_user),
):
    """
    Create and validate a relationship between two database columns.

    Only schema metadata is used.

    No business records are read.
    No SELECT * is performed.
    No customer/business data is stored.
    """

    try:
        relationship = create_relationship(
            request.relationship,
            request.schema_metadata,
        )

        return {
            "message": (
                "Relationship created successfully."
            ),
            "relationship": relationship,
        }

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to create relationship.",
        ) from exc