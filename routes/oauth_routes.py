from fastapi import APIRouter, Depends, HTTPException, status
from starlette.requests import Request
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from authlib.integrations.starlette_client import OAuth, OAuthError
import os, secrets

from core.database import get_db
from models.models import User
from utils.security import create_access_token, get_password_hash

oauth_router = APIRouter(prefix="/oauth", tags=["oauth"])

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")

oauth = OAuth()
oauth.register(
    name="google",
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_id=GOOGLE_CLIENT_ID,
    client_secret=GOOGLE_CLIENT_SECRET,
    client_kwargs={"scope": "openid email profile"},
)

@oauth_router.get("/google/login")
async def google_login(request: Request):
    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Google OAuth not configured (missing GOOGLE_CLIENT_ID/GOOGLE_CLIENT_SECRET).",
        )
    redirect_uri = request.url_for("google_callback")
    return await oauth.google.authorize_redirect(request, redirect_uri)

@oauth_router.get("/google/callback", name="google_callback")
async def google_callback(
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Fluxo com auto-signup:
    - Se o e-mail do Google existir: gera JWT.
    - Se não existir: cria usuário básico e gera JWT.
    """
    try:
        token = await oauth.google.authorize_access_token(request)
    except OAuthError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"OAuth error: {getattr(e, 'error', str(e))}",
        )

    userinfo = token.get("userinfo")
    if not userinfo:
        resp = await oauth.google.get("userinfo", token=token)
        userinfo = resp.json()

    email = (userinfo or {}).get("email")
    name = (userinfo or {}).get("name") or (email.split("@")[0] if email else None)
    avatar = (userinfo or {}).get("picture")

    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Google did not return an email"
        )

    # 1) Tenta achar usuário existente
    user = db.query(User).filter(User.email == email).first()

    # 2) Se não existir, cria (cpf opcional; senha randômica apenas para preencher hashed_password)
    if not user:
        try:
            random_password = secrets.token_urlsafe(32)
            user = User(
                name=name or "Google User",
                email=email,
                hashed_password=get_password_hash(random_password),
                cpf=None,
                phone=None,
                avatar=avatar,
                is_active=True,
                is_admin=False,
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        except IntegrityError:
            # condição de corrida: outro request criou o mesmo e-mail
            db.rollback()
            user = db.query(User).filter(User.email == email).first()
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Could not create user for this Google account.",
                )

    access_token = create_access_token(subject=str(user.id))
    return {"access_token": access_token, "token_type": "bearer"}
