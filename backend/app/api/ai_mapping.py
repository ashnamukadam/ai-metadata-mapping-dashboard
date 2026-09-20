from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status

from app.auth.dependencies import get_current_user
from app.schemas.ai_mapping import (
    AIMappingRequest,
    AIMappingResponse,
    BusinessMappingResult,
    ColumnMappingResult,
)
from app.services.ai_mapping_service import (
    generate_business_mapping,
    generate_column_mapping,
)


# ============================================================
# ROUTER
# ============================================================

router = APIRouter(
    prefix="/database",
    tags=["AI Mapping"],
)


# ============================================================
# AI MAPPING
# ============================================================

@router.post(
    "/ai-mapping",
    response_model=AIMappingResponse,
    status_code=status.HTTP_200_OK,
)
def create_ai_mapping(
    request: AIMappingRequest,
    current_user: Any = Depends(
        get_current_user
    ),
):

    try:

        # ----------------------------------------------------
        # BUSINESS MAPPING
        # ----------------------------------------------------

        if request.mapping_type == "business_mapping":

            result = generate_business_mapping(
                request
            )

            return {
                "message": (
                    "AI business mapping generated "
                    "successfully."
                ),
                "mapping_type": (
                    "business_mapping"
                ),
                "table_name": (
                    request.table_name
                ),
                "business_mapping": (
                    BusinessMappingResult(
                        **result
                    )
                ),
                "column_mappings": None,
            }


        # ----------------------------------------------------
        # COLUMN MAPPING
        # ----------------------------------------------------

        if request.mapping_type == "column_mapping":

            result = generate_column_mapping(
                request
            )

            return {
                "message": (
                    "AI column mapping generated "
                    "successfully."
                ),
                "mapping_type": (
                    "column_mapping"
                ),
                "table_name": (
                    request.table_name
                ),
                "business_mapping": None,
                "column_mappings": [
                    ColumnMappingResult(
                        **item
                    )
                    for item in result
                ],
            }


        # ----------------------------------------------------
        # INVALID TYPE
        # ----------------------------------------------------

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid mapping type.",
        )


    except ValueError as exc:

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


    except Exception as exc:

        print(
            "AI MAPPING ERROR:",
            repr(exc)
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=(
                "Unable to generate AI mapping."
            ),
        ) from exc