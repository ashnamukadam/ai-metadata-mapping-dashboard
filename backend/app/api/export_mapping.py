from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.database.session import get_db
from app.schemas.export_mapping import ExportMappingRequest
from app.services.export_mapping_service import (
    build_export_mapping,
    generate_mapping_json,
    generate_mapping_txt,
)


router = APIRouter(
    prefix="/database",
    tags=["Export Mapping"],
)


@router.post(
    "/export-mapping",
    status_code=status.HTTP_200_OK,
)
def export_mapping(
    request: ExportMappingRequest,
    current_user: Any = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Export the authenticated user's persisted metadata mapping.

    Only mapping configuration is exported.

    Never exports:
    - Business records
    - Database credentials
    - Passwords
    - Secrets
    - Tokens
    """

    try:
        # Build the export from persisted mappings.
        persisted_mapping = build_export_mapping(
            database=request.database,
            db=db,
            user_id=current_user.id,
        )

        # Preserve the format requested by the caller.
        persisted_mapping.format = request.format

        if request.format == "json":
            content = generate_mapping_json(
                persisted_mapping
            )

            return Response(
                content=content,
                media_type="application/json",
                headers={
                    "Content-Disposition": (
                        'attachment; filename="mapping.json"'
                    )
                },
            )

        if request.format == "txt":
            content = generate_mapping_txt(
                persisted_mapping
            )

            return Response(
                content=content,
                media_type="text/plain",
                headers={
                    "Content-Disposition": (
                        'attachment; filename="mapping.txt"'
                    )
                },
            )

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Unsupported export format. "
                "Use 'txt' or 'json'."
            ),
        )

    except HTTPException:
        raise

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to export mapping.",
        ) from exc