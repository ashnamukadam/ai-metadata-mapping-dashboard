from sqlalchemy.orm import Session
from app.models.user import User
from app.schemas.user import UserCreate


def create_user(db: Session, user: UserCreate):
    db_user = User(
        name=user.name,
        email=user.email,
        password_hash=user.password
    )

    try:
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user

    except Exception as e:
        db.rollback()
        print("DATABASE ERROR:", repr(e))
        raise