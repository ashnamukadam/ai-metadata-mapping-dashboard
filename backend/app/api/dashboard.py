from fastapi import APIRouter, Depends

from app.auth.dependencies import get_current_user
from app.schemas.dashboard import DashboardResponse
from app.services.dashboard_service import get_dashboard_data

router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard"]
)


@router.get(
    "",
    response_model=DashboardResponse
)
def get_dashboard(
    current_user=Depends(get_current_user)
):
    """
    Returns dashboard statistics.
    User must be logged in.
    """

    return get_dashboard_data()