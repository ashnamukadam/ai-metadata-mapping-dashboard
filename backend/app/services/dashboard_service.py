from app.schemas.dashboard import DashboardResponse



def get_connected_databases() -> int:
    """
    Returns total connected databases.
    Will query PostgreSQL in Module 3.
    """
    return 0


def get_last_mapping_date():
    """
    Returns latest mapping date.
    Will query mappings table in Module 7.
    """
    return None


def get_total_tables() -> int:
    """
    Returns total extracted tables.
    Will query metadata tables in Module 5.
    """
    return 0


def get_total_mapped_tables() -> int:
    """
    Returns total mapped tables.
    Will query business mappings in Module 7.
    """
    return 0


def get_dashboard_data() -> DashboardResponse:
    return DashboardResponse(
        connected_databases=get_connected_databases(),
        last_mapping_date=get_last_mapping_date(),
        total_tables=get_total_tables(),
        total_mapped_tables=get_total_mapped_tables()
    )