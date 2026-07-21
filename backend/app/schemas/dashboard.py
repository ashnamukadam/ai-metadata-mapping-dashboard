from pydantic import BaseModel
from typing import Optional


class DashboardResponse(BaseModel):
    connected_databases: int
    last_mapping_date: Optional[str] = None
    total_tables: int
    total_mapped_tables: int