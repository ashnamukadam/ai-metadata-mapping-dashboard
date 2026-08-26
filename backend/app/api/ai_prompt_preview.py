from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.auth.dependencies import get_current_user
from app.schemas.ai_prompt_preview import (
    AIPromptPreviewRequest,
    AIPromptPreviewResponse,
)
from app.services.ai_prompt_preview_service import (
    generate_ai_prompt_preview,
)


router = APIRouter(
    prefix="/database",
    tags=["AI Prompt Preview"],
)


@router.post(
    "/ai-prompt-preview",
    response_model=AIPromptPreviewResponse,
    status_code=status.HTTP_200_OK,
)
def create_ai_prompt_preview(
    request: AIPromptPreviewRequest,
    current_user: Any = Depends(get_current_user),
):
    """
    Generate a deterministic AI prompt preview.

    No AI model is used.
    No database records are accessed.
    No business data is read or stored.
    """

    try:
        preview = generate_ai_prompt_preview(request)

        return {
            "message": (
                "AI prompt preview generated successfully."
            ),
            "preview": preview,
        }

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to generate AI prompt preview.",
        ) from exc