from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status

from app.auth.dependencies import get_current_user
from app.schemas.database_connection import DatabaseConnectionRequest
from app.services.permission_validation_service import (
    validate_metadata_permission,
)


router = APIRouter(
    prefix="/database",
    tags=["Database Permission Validation"],
)


@router.post(
    "/validate-permission",
    status_code=status.HTTP_200_OK,
)
def validate_database_metadata_permission(
    connection: DatabaseConnectionRequest,
    current_user: Any = Depends(get_current_user),
):
    """
    Validate metadata-only access to the user's database.

    This endpoint must never:
    - read business records
    - execute SELECT * against business tables
    - cache customer/business data
    - export business data

    Only database metadata is accessed.
    """

    try:
        result = validate_metadata_permission(connection)

        return {
            "message": result.message,
            "database_type": result.database_type,
            "database_name": result.database_name,
            "connected": result.connected,
            "metadata_access": result.metadata_access,
            "metadata_only": result.metadata_only,
        }

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
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Metadata permission validation failed.",
        ) from exc