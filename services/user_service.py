from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status

from models.models import User
from schemas.user_schemas import UserSignUp, UserUpdateMe
from utils.security import get_password_hash, verify_password


def create_user(db: Session, user_in: UserSignUp) -> User:
    """
    Cria usuário confiando na UNIQUE constraint do banco (email/cpf).
    Evita SELECTs prévios e trata duplicidade via IntegrityError.
    """
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
    try:
        db.commit()
    except IntegrityError as e:
        db.rollback()
        constraint = getattr(getattr(e, "orig", None), "diag", None)
        c_name = getattr(constraint, "constraint_name", None)

        msg = str(getattr(e, "orig", e)).lower()

        if (c_name and "email" in c_name.lower()) or "email" in msg:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )
        if (c_name and "cpf" in c_name.lower()) or "cpf" in msg:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="CPF already registered",
            )

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unique constraint violated",
        ) from e

    db.refresh(user)
    return user


def authenticate(db: Session, email: str, password: str) -> User | None:
    user = db.query(User).filter(User.email == email).first()
    if user and verify_password(password, user.hashed_password):
        return user
    return None


def update_user_me(db: Session, user: User, payload: UserUpdateMe) -> User:
    user.name = payload.name
    if payload.email is not None:
        user.email = payload.email
    if payload.phone is not None:
        user.phone = payload.phone
    if payload.avatar is not None:
        user.avatar = payload.avatar

    try:
        db.commit()
    except IntegrityError as e:
        db.rollback()
        constraint = getattr(getattr(e, "orig", None), "diag", None)
        c_name = getattr(constraint, "constraint_name", None)
        msg = str(getattr(e, "orig", e)).lower()

        if (c_name and "email" in c_name.lower()) or "email" in msg:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unique constraint violated",
        ) from e

    db.refresh(user)
    return user


def deactivate_user_me(db: Session, user: User) -> None:
    if not user.is_active:
        return
    user.is_active = False
    db.commit()


def hard_delete_user_me(db: Session, user: User) -> None:
    db.delete(user)
    try:
        db.commit()
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot hard delete user due to related records (FK). Try soft delete instead.",
        ) from e