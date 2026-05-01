# app/api/routes/user.py
from fastapi import APIRouter, Depends
from app.schemas.user import UserResponse
from app.db.models.user import User
from app.core.dependencies import get_current_user

router = APIRouter()


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user
