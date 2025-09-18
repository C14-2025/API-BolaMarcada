from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
from typing import Optional
import uuid
from typing import Union
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from passlib.context import CryptContext

from core.config import settings
from core.database import get_db
from models.models import User


oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/users/token")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# 1) Mantém o OAuth2 (password) para login automático via Swagger
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/users/token",  # /api/v1/users/token
    auto_error=False,  # <- importante para não dar 401 automático se vier pelo Bearer
)

# 2) Adiciona HTTP Bearer para colar token manualmente
http_bearer = HTTPBearer(auto_error=False)

def _pick_token(
    oauth2_token: str | None,
    bearer_creds: HTTPAuthorizationCredentials | None,
) -> str:
    # Prioriza o que veio no Authorization: Bearer <token>
    if bearer_creds and bearer_creds.scheme and bearer_creds.credentials:
        if bearer_creds.scheme.lower() == "bearer":
            return bearer_creds.credentials
    # Se não veio pelo header, usa o token do OAuth2 (Authorize → username/password)
    if oauth2_token:
        return oauth2_token
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated",
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_current_user(
    db: Session = Depends(get_db),
    oauth2_token: str | None = Depends(oauth2_scheme),
    bearer_creds: HTTPAuthorizationCredentials | None = Depends(http_bearer),
) -> User:
    token = _pick_token(oauth2_token, bearer_creds)

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        sub = payload.get("sub")
        if not sub:
            raise ValueError("missing sub")
        user_id = uuid.UUID(str(sub))
    except (JWTError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user")
    return user


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(
    subject: Union[str, int, uuid.UUID], expires_delta: Optional[timedelta] = None
) -> str:
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )
    return encoded_jwt


def decode_access_token(token: str) -> Optional[str]:
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        return payload.get("sub")
    except JWTError:
        return None
