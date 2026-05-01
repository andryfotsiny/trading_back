# app/services/auth/auth_service.py
from sqlalchemy.orm import Session
from app.db.models.user import User
from app.core.security import get_password_hash, verify_password, create_access_token


def create_user(db: Session, email: str, username: str, password: str) -> User:
    user = User(
        email=email,
        username=username,
        hashed_password=get_password_hash(password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, email: str, password: str):
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(password, user.hashed_password):
        return None
    return user


def get_user_by_id(db: Session, user_id: int):
    return db.query(User).filter(User.id == user_id).first()


def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()


def generate_token(user: User) -> dict:
    token = create_access_token(data={"sub": str(user.id)})
    return {"access_token": token, "token_type": "bearer"}
