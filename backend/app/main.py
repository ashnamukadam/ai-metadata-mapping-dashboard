from fastapi import FastAPI
from app.api.auth import router as auth_router

app = FastAPI(
    title="AI Metadata Mapping Dashboard API",
    version="1.0.0",
)
app.include_router(auth_router)

@app.get("/")
async def root():
    return {
        "status": "success",
        "message": "Backend is running!"
    }