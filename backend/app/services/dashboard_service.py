from app.schemas.dashboard import DashboardResponse


def get_dashboard_data() -> DashboardResponse:
    """
    Returns dashboard statistics.
    Dummy values for now.
    """

    return DashboardResponse(
        connected_databases=0,
        last_mapping_date=None,
        total_tables=0,
        total_mapped_tables=0,
    )