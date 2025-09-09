from sqlalchemy.orm import Session
from models.models import User
from schemas.user_schemas import UserSignUp
from utils.security import get_password_hash, verify_password
from fastapi import HTTPException, status



def create_user(db: Session, user_in: UserSignUp) -> User:

    if db.query(User).filter(User.email == user_in.email).first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    if db.query(User).filter(User.cpf == user_in.cpf).first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="CPF already registered")

    hashed_password = get_password_hash(user_in.password)

    user = User(
        name=user_in.name,
        email=user_in.email,
        cpf=user_in.cpf,
        phone=user_in.phone,
        avatar=user_in.avatar or "default_avatar.png",
        hashed_password=hashed_password,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def authenticate(db: Session, email: str, password: str) -> User | None:
    user = db.query(User).filter(User.email == email).first()
    if user and verify_password(password, user.hashed_password):
        return user
    return None
