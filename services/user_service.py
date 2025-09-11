# services/user_service.py
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status

from models.models import User
from schemas.user_schemas import UserSignUp
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
        # is_active / is_admin usam defaults do modelo
    )

    db.add(user)
    try:
        db.commit()
    except IntegrityError as e:
        db.rollback()
        # Tenta identificar qual campo violou a UNIQUE, funciona bem em Postgres.
        # Em SQLite, cai no fallback pelo conteúdo da mensagem.
        constraint = getattr(getattr(e, "orig", None), "diag", None)
        c_name = getattr(constraint, "constraint_name", None)

        # Heurísticas por constraint/mensagem:
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

        # Genérico (ex.: outra UNIQUE que porventura exista)
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
