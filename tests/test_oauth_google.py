import uuid
from types import SimpleNamespace
import pytest
from unittest.mock import AsyncMock
from starlette.responses import RedirectResponse
from models.models import User
from utils.security import decode_access_token

API_PREFIX = "/api/v1"

def test_google_login_redirect(client, monkeypatch):
    """
    Deve redirecionar para o Google (302/307).
    """
    import routes.oauth_routes as oauth_routes

    # Considera configurado
    monkeypatch.setattr(oauth_routes, "GOOGLE_CLIENT_ID", "fake-client-id")
    monkeypatch.setattr(oauth_routes, "GOOGLE_CLIENT_SECRET", "fake-secret")

    async def fake_authorize_redirect(request, redirect_uri, **kwargs):
        return RedirectResponse(url="https://example.com/oauth2/authorize")

    monkeypatch.setattr(
        oauth_routes.oauth.google,
        "authorize_redirect",
        AsyncMock(side_effect=fake_authorize_redirect),
    )

    # starlette TestClient usa follow_redirects
    r = client.get(f"{API_PREFIX}/oauth/google/login", follow_redirects=False)
    assert r.status_code in (302, 307)
    assert "location" in r.headers


def test_google_callback_auto_signup_creates_user_and_returns_jwt(client, db_session, monkeypatch):
    """
    Primeira vez: não existe usuário -> cria e retorna nosso JWT.
    """
    import routes.oauth_routes as oauth_routes

    test_email = "oauthuser@example.com"
    token = {"userinfo": {"email": test_email, "name": "OAuth User", "picture": "http://img"}}

    monkeypatch.setattr(
        oauth_routes.oauth.google,
        "authorize_access_token",
        AsyncMock(return_value=token),
    )

    # garante inexistente
    assert db_session.query(User).filter(User.email == test_email).first() is None

    r = client.get(f"{API_PREFIX}/oauth/google/callback?code=fake&state=fake")
    assert r.status_code == 200, r.text
    data = r.json()
    assert data.get("token_type") == "bearer"
    access_token = data["access_token"]

    sub = decode_access_token(access_token)
    if isinstance(sub, dict):
        sub = sub.get("sub")
    uuid.UUID(str(sub))  # valida UUID

    user = db_session.query(User).filter(User.email == test_email).first()
    assert user is not None
    assert str(user.id) == str(sub)


def test_google_callback_existing_user_returns_jwt(client, db_session, monkeypatch):
    """
    Usuário já existe: não cria novo, apenas retorna JWT do existente.
    """
    import routes.oauth_routes as oauth_routes

    email = "existing@example.com"
    u = User(
        id=uuid.uuid4(),
        name="Exist User",
        email=email,
        hashed_password="x",
        cpf=None,
        phone=None,
        is_active=True,   
        is_admin=False, 
        avatar=None,
    )
    db_session.add(u)
    db_session.commit()

    token = {"userinfo": {"email": email, "name": "Exist User"}}
    monkeypatch.setattr(
        oauth_routes.oauth.google,
        "authorize_access_token",
        AsyncMock(return_value=token),
    )

    r = client.get(f"{API_PREFIX}/oauth/google/callback?code=fake&state=fake")
    assert r.status_code == 200, r.text
    data = r.json()
    sub = decode_access_token(data["access_token"])
    if isinstance(sub, dict):
        sub = sub.get("sub")
    assert str(sub) == str(u.id)

    count = db_session.query(User).filter(User.email == email).count()
    assert count == 1


def test_google_callback_missing_email_400(client, monkeypatch):
    """
    Se o Google não retornar e-mail, endpoint deve falhar com 400.
    """
    import routes.oauth_routes as oauth_routes

    token = {"userinfo": {}}  # sem email

    # Mocka access_token
    monkeypatch.setattr(
        oauth_routes.oauth.google,
        "authorize_access_token",
        AsyncMock(return_value=token),
    )

    # Mocka também o .get("userinfo") para não bater na rede nem exigir access_token real
    class FakeResp:
        def json(self):
            return {}  # segue sem email

    monkeypatch.setattr(
        oauth_routes.oauth.google,
        "get",
        AsyncMock(return_value=FakeResp()),
    )

    r = client.get(f"{API_PREFIX}/oauth/google/callback?code=fake&state=fake")
    assert r.status_code == 400
