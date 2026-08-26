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
from app.api.business_mapping import router as business_mapping_router
from app.api.column_mapping import router as column_mapping_router
from app.api.relationship import router as relationship_router
from app.api.ai_prompt_preview import router as ai_prompt_preview_router


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
app.include_router(business_mapping_router)
app.include_router(column_mapping_router)
app.include_router(relationship_router)
app.include_router(ai_prompt_preview_router)



@app.get("/")
async def root():
    return {
        "status": "success",
        "message": "Backend is running!",
    }