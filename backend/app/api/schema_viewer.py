from fastapi import APIRouter, Depends, HTTPException

from app.auth.dependencies import get_current_user
from app.services.schema_viewer_service import build_schema_view


router = APIRouter(
    prefix="/database",
    tags=["Schema Viewer"],
)


@router.post("/schema-view")
async def view_database_schema(
    metadata: dict,
    current_user=Depends(get_current_user),
):
    """
    Display database schema hierarchy:

    Database
        ↓
    Tables
        ↓
    Columns

    Only metadata is returned.
    Business records are never returned.
    """

    if not metadata:
        raise HTTPException(
            status_code=400,
            detail="Metadata is required.",
        )

    try:
        schema = build_schema_view(metadata)

        return {
            "message": "Database schema viewer generated successfully.",
            "schema": schema,
            "metadata_only": True,
        }

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Unable to generate schema viewer.",
        )