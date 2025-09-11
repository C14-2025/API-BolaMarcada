from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from core.database import get_db
from schemas.user_schemas import (
    UserSignIn,
    UserSignUp,
    UserResponse,
    UserResponseToken,
)
from services.user_service import create_user, authenticate
from utils.security import create_access_token

user_router = APIRouter(prefix="/users", tags=["users"])


@user_router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def signup(user_in: UserSignUp, db: Session = Depends(get_db)):
    user = create_user(db, user_in)
    return user


@user_router.post("/signin", response_model=UserResponseToken, status_code=status.HTTP_200_OK)
def signin(user_in: UserSignIn, db: Session = Depends(get_db)):
    user = authenticate(db, user_in.email, user_in.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    access_token = create_access_token(subject=str(user.id))
    return {"access_token": access_token, "token_type": "bearer"}
