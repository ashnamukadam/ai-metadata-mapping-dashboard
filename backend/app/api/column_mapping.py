from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.auth.dependencies import get_current_user
from app.schemas.column_mapping import (
    ColumnMappingRequest,
    ColumnMappingResponse,
)
from app.services.column_mapping_service import (
    create_column_mapping,
)


class ColumnMappingWithMetadataRequest(BaseModel):
    mapping: ColumnMappingRequest
    schema_metadata: dict[str, Any]


router = APIRouter(
    prefix="/database",
    tags=["Column Mapping"],
)


@router.post(
    "/column-mapping",
    response_model=ColumnMappingResponse,
    status_code=status.HTTP_200_OK,
)
def create_mapping(
    request: ColumnMappingWithMetadataRequest,
    current_user: Any = Depends(get_current_user),
):
    """
    Create and validate a business mapping for one database column.

    Only schema metadata is used.

    No business records are read.
    No SELECT * is performed.
    No customer/business data is stored.
    """

    try:
        mapping = create_column_mapping(
            request.mapping,
            request.schema_metadata,
        )

        return {
            "message": (
                "Column mapping created successfully."
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
            detail="Unable to create column mapping.",
        ) from exc