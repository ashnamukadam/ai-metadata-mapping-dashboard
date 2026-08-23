from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status

from app.auth.dependencies import get_current_user
from app.schemas.database_connection import DatabaseConnectionRequest
from app.schemas.metadata import MetadataExtractionResponse
from app.services.database_connection_service import (
    check_database_connection,
)
from app.services.metadata_extraction_service import (
    extract_database_metadata,
)


router = APIRouter(
    prefix="/database",
    tags=["Schema Extraction"],
)


@router.post(
    "/metadata",
    response_model=MetadataExtractionResponse,
    status_code=status.HTTP_200_OK,
)
def extract_metadata(
    connection: DatabaseConnectionRequest,
    current_user: Any = Depends(get_current_user),
):
    """
    Extract database schema metadata only.

    Allowed:
    - Database name
    - Tables
    - Views
    - Columns
    - Primary keys
    - Foreign keys
    - Indexes
    - Column types
    - Nullable information
    - Auto-increment information
    - Constraints

    Never:
    - SELECT *
    - Read business records
    - Return business data
    - Cache business data
    - Return credentials
    """

    try:
        # ----------------------------------------------------
        # STEP 1 — VERIFY CONNECTION FIRST
        # ----------------------------------------------------

        connection_result = check_database_connection(
            connection
        )

        if isinstance(connection_result, dict):
            connected = bool(
                connection_result.get(
                    "connected",
                    False,
                )
            )
        else:
            connected = bool(connection_result)

        if not connected:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Database connection could not be "
                    "established."
                ),
            )

        # ----------------------------------------------------
        # STEP 2 — EXTRACT METADATA ONLY
        # ----------------------------------------------------

        metadata = extract_database_metadata(
            connection
        )

        return {
            "message": (
                "Database schema metadata extracted "
                "successfully."
            ),
            "metadata": metadata,
            "metadata_only": True,
        }

    except HTTPException:
        raise

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    except PermissionError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        # Never expose raw database errors,
        # credentials, connection strings,
        # or stack traces.
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=(
                "Database schema metadata extraction failed."
            ),
        ) from exc