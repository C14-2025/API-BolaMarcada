from fastapi import APIRouter, Depends, HTTPException, status
from schemas.user_schemas import UserSignUp, UserResponse, UserResponseToken, UserSignIn
from sqlalchemy.orm import Session
from core.database import get_db
from models.models import User
from services.user_service import create_user
from utils.security import create_access_token, verify_password

user_router = APIRouter(prefix="/users", tags=["users"])


@user_router.post(
    "/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED
)
def signup(user_in: UserSignUp, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.email == user_in.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered"
        )
    user = create_user(db, user_in)
    return user


@user_router.post(
    "/login", response_model=UserResponseToken, status_code=status.HTTP_200_OK
)
def login(user_in: UserSignIn, db: Session = Depends(get_db)):

    user = db.query(User).filter(User.email == user_in.email).first()
    if not user or not verify_password(user_in.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    access_token = create_access_token(subject=str(user.id))
    return {"access_token": access_token, "token_type": "bearer"}
