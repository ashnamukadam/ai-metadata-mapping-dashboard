from fastapi import FastAPI

from app.api.auth import router as auth_router
from app.api.dashboard import router as dashboard_router

app = FastAPI(
    title="AI Metadata Mapping Dashboard API",
    version="1.0.0",
)

# Authentication Routes
app.include_router(auth_router)

# Dashboard Routes
app.include_router(dashboard_router)


@app.get("/")
async def root():
    return {
        "status": "success",
        "message": "Backend is running!"
    }