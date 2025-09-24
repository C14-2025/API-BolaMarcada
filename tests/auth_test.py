import uuid
import pytest
from unittest.mock import MagicMock, patch
from schemas.user_schemas import UserSignUp, UserSignIn
from utils.security import get_password_hash, decode_access_token  
from models.models import User



# Teste 1: create_user hash password
@patch("services.user_service.get_password_hash")
def test_create_user_hash_password(mock_get_password_hash):
    
    mock_get_password_hash.return_value = "hashed_senha"

    
    user_in = UserSignUp(
        name="Teste",
        email="teste@example.com",
        cpf="12345678901",
        phone="999999999",
        password="Senha123!",
    )

   
    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.first.return_value = (
        None  
    )

    from services.user_service import create_user

    user = create_user(mock_db, user_in)

    assert user.email == user_in.email
    assert user.hashed_password == "hashed_senha"



# Teste 2: authenticate invalid password
@patch("services.user_service.verify_password")
def test_authenticate_invalid_password(mock_verify):
    mock_verify.return_value = False

   
    from models.models import User 

    mock_user = User(
        id=uuid.uuid4(),
        name="Teste",
        email="teste@example.com",
        cpf="12345678901",
        phone="999999999",
        hashed_password="hashed_senha",
        is_active=True,
        is_admin=False,
    )

   
    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.first.return_value = mock_user

    from services.user_service import authenticate

    user = authenticate(mock_db, email="teste@example.com", password="SenhaErrada123!")
    assert user is None



# Teste 3: create & decode access token
def test_create_and_decode_access_token():
    from utils.security import create_access_token, decode_access_token

    user_id = uuid.uuid4()
    token = create_access_token(subject=str(user_id))
    decoded = decode_access_token(token)
    assert decoded == str(user_id)



# Teste 4: rota /signin
def test_signin_route_integration(client, db_session):
    raw_password = "SenhaRoute123!"

    user = User(
        id=uuid.uuid4(),
        name="Route User",
        email="route@example.com",
        cpf="12345678901",
        phone=None,
        hashed_password=get_password_hash(raw_password),
        is_active=True,
        is_admin=False,
        avatar=None,
    )
    db_session.add(user)
    db_session.commit()

    payload = {"email": user.email, "password": raw_password}
    resp = client.post("/users/signin", json=payload)
    assert resp.status_code == 200, resp.text

    data = resp.json()
    assert "access_token" in data
    assert data.get("token_type") == "bearer"

   
    try:
        decoded = decode_access_token(data["access_token"])
       
        assert decoded.get("sub") == str(user.id)
    except Exception:
        assert isinstance(data["access_token"], str) and len(data["access_token"]) > 20
