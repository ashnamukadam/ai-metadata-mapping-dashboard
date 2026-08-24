from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.auth.dependencies import get_current_user
from app.schemas.business_mapping import (
    BusinessMappingRequest,
    BusinessMappingResponse,
)
from app.services.business_mapping_service import (
    create_business_mapping,
)


router = APIRouter(
    prefix="/database",
    tags=["Business Mapping"],
)


class BusinessMappingWithMetadataRequest(BaseModel):
    mapping: BusinessMappingRequest
    schema_metadata: dict[str, Any]


@router.post(
    "/business-mapping",
    response_model=BusinessMappingResponse,
    status_code=status.HTTP_200_OK,
)
def create_mapping(
    request: BusinessMappingWithMetadataRequest,
    current_user: Any = Depends(get_current_user),
):
    """
    Create and validate a business mapping using
    previously extracted database schema metadata.

    Only schema metadata is used.

    No business records are read.
    No SELECT * is performed.
    No customer/business data is stored.
    """

    try:
        mapping = create_business_mapping(
            request.mapping,
            request.schema_metadata,
        )

        return {
            "message": (
                "Business mapping created successfully."
            ),
            "mapping": mapping,
        }

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to create business mapping.",
        ) from exc