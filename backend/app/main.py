from fastapi import FastAPI

from app.api.auth import router as auth_router
from app.api.dashboard import router as dashboard_router
from app.api.database_connection import router as database_connection_router


app = FastAPI(
    title="AI Metadata Mapping Dashboard API",
    version="1.0.0",
)

app.include_router(auth_router)
app.include_router(dashboard_router)
app.include_router(database_connection_router)


@app.get("/")
async def root():
    return {
        "status": "success",
        "message": "Backend is running!"
    }