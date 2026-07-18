from sqlalchemy import text
from fastapi import HTTPException
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.user import UserCreate
from app.services.user_service import create_user

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)

@router.get("/test")
def test_auth():
    return {"message": "Authentication router is working!"}


@router.get("/db-test")
def db_test(db: Session = Depends(get_db)):
    try:
        result = db.execute(text("SELECT 1")).scalar()
        return {"database": "Connected", "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/register")
def register(
    user: UserCreate,
    db: Session = Depends(get_db)
):
    try:
        return create_user(db, user)
    except Exception as e:
        print("ERROR:", repr(e))
        raise