from fastapi import FastAPI

from app.api.auth import router as auth_router
from app.api.dashboard import router as dashboard_router
from app.api.database_connection import (
    router as database_connection_router,
)
from app.api.database_permission import (
    router as database_permission_router,
)
from app.api.metadata_extraction import (
    router as metadata_extraction_router,
)
from app.api.schema_viewer import router as schema_viewer_router


app = FastAPI(
    title="AI Metadata Mapping Dashboard API",
    version="1.0.0",
)


app.include_router(auth_router)
app.include_router(dashboard_router)
app.include_router(database_connection_router)
app.include_router(database_permission_router)
app.include_router(metadata_extraction_router)
app.include_router(schema_viewer_router)


@app.get("/")
async def root():
    return {
        "status": "success",
        "message": "Backend is running!",
    }