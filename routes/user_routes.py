from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm
from core.database import get_db
from models.models import User
from schemas.user_schemas import (
    UserSignIn,
    UserSignUp,
    UserResponse,
    UserResponseToken,
    UserUpdateMe,
    UserPublic,
)
from services.user_service import (
    create_user,
    authenticate,
    update_user_me,
    deactivate_user_me,
    hard_delete_user_me,
)
from utils.security import create_access_token, get_current_user
import uuid

user_router = APIRouter(prefix="/users", tags=["users"])


@user_router.get("/me", response_model=UserPublic, status_code=status.HTTP_200_OK)
def get_me(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retorna os dados públicos do usuário autenticado.
    """
    return current_user


@user_router.get("/{user_id}", response_model=UserPublic, status_code=status.HTTP_200_OK)
def get_user_by_id(
    user_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    """
    Retorna os dados públicos de um usuário pelo ID.
    """
    user = db.query(User).filter(User.id == user_id, User.is_active == True).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return user


@user_router.post(
    "/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED
)
def signup(user_in: UserSignUp, db: Session = Depends(get_db)):
    user = create_user(db, user_in)
    return user


@user_router.post(
    "/signin", response_model=UserResponseToken, status_code=status.HTTP_200_OK
)
def signin(user_in: UserSignIn, db: Session = Depends(get_db)):
    user = authenticate(db, user_in.email, user_in.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    access_token = create_access_token(subject=str(user.id))
    return {"access_token": access_token, "token_type": "bearer"}


@user_router.post(
    "/token", response_model=UserResponseToken, status_code=status.HTTP_200_OK
)
def login_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    # OAuth2 usa "username" para o login; mapeamos para seu "email"
    user = authenticate(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    access_token = create_access_token(subject=str(user.id))
    return {"access_token": access_token, "token_type": "bearer"}


@user_router.patch("/me", response_model=UserPublic, status_code=status.HTTP_200_OK)
def update_me(
    payload: UserUpdateMe,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Atualiza os dados do usuário autenticado.
    Campos atualizáveis: name (obrigatório), email, phone, avatar.
    Trata e-mail duplicado via IntegrityError.
    """
    updated = update_user_me(db, current_user, payload)
    return updated


@user_router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
def delete_me(
    soft: bool = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Deleta a conta do usuário autenticado.
    - soft=True (default): desativa a conta (active=False).
    - soft=False: tenta hard delete (pode falhar por FKs).
    """
    if soft:
        deactivate_user_me(db, current_user)
    else:
        hard_delete_user_me(db, current_user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
