from sqlalchemy.orm import Session

from app.models.user import User
from app.schemas.user import UserCreate
from app.auth.password import hash_password


def create_user(db: Session, user: UserCreate):
    db_user = User(
        name=user.name,
        email=user.email,
        password_hash=hash_password(user.password)
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


def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()


def update_password(db: Session, email: str, new_password: str):
    user = get_user_by_email(db, email)

    if user is None:
        return None

    user.password_hash = hash_password(new_password)

    db.commit()
    db.refresh(user)

    return user