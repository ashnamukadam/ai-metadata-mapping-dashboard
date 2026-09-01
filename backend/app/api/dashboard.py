from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.database.session import get_db
from app.schemas.dashboard import DashboardResponse
from app.services.dashboard_service import get_dashboard_data


router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard"],
)


@router.get(
    "",
    response_model=DashboardResponse,
)
def get_dashboard(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Return dashboard statistics for the authenticated user.
    """

    return get_dashboard_data(
        db=db,
        user_id=current_user.id,
    )