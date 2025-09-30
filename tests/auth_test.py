import uuid
from unittest.mock import MagicMock, patch
from schemas.user_schemas import UserSignUp, UserSignIn
from utils.security import get_password_hash, decode_access_token
from models.models import User
from tests.tests_utils import make_client


ROUTES_MODULE = "routes.user_routes"
API_PREFIX = "/api/v1"


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
    mock_db.query.return_value.filter.return_value.first.return_value = None

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


# Teste 3: authenticate valid password
@patch("services.user_service.verify_password")
def test_authenticate_valid_password(mock_verify):
    mock_verify.return_value = True  # senha válida

    from models.models import User
    import uuid

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

    # Simula usuário existente no banco
    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.first.return_value = mock_user

    from services.user_service import authenticate

    # Senha fornecida correta
    user = authenticate(mock_db, email="teste@example.com", password="Senha123!")

    # Agora deve autenticar com sucesso e retornar o usuário
    assert user is not None
    assert user.email == "teste@example.com"


# Teste 3: create & decode access token
def test_create_and_decode_access_token():
    from utils.security import create_access_token, decode_access_token

    user_id = uuid.uuid4()
    token = create_access_token(subject=str(user_id))
    decoded = decode_access_token(token)
    assert decoded == str(user_id)


# Teste 4: rota /token integração
def test_token_route_integration(client, db_session):
    from models.models import User
    from utils.security import get_password_hash, decode_access_token

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

    resp = client.post(
        "/api/v1/users/token",
        data={"username": user.email, "password": raw_password},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data.get("token_type") == "bearer"
    assert "access_token" in data
    decoded = decode_access_token(data["access_token"])
    assert decoded == str(user.id) or decoded.get("sub") == str(user.id)


# Teste 5: rota /users/me integração
def test_update_me_route_success():
    client = make_client()

    with patch("routes.user_routes.update_user_me") as mock_update:
        fake_id = uuid.uuid4()
        mock_update.return_value = {
            "id": str(fake_id),
            "name": "Jane Doe",
            "email": "jane@example.com",
            "phone": "+5511999999999",
            "avatar": "https://cdn.example.com/avatar.png",
            "is_active": True,
            "cpf": "12345678901",
        }

        payload = {
            "name": "Jane Doe",
            "email": "jane@example.com",
            "phone": "+5511999999999",
            "avatar": "https://cdn.example.com/avatar.png",
        }

        r = client.patch(f"{API_PREFIX}/users/me", json=payload)
        assert r.status_code == 200, r.text

        data = r.json()
        assert data["id"] == str(fake_id)
        assert data["name"] == "Jane Doe"
        assert data["email"] == "jane@example.com"

        args, _ = mock_update.call_args
        assert len(args) == 3
        assert getattr(args[1], "email", None) == "auth@example.com"

# Teste 6: rota DELETE /users/me integração (soft delete padrão)
def test_delete_me_route_soft_default_204():
    client = make_client()

    with patch("routes.user_routes.deactivate_user_me") as mock_soft, patch(
        "routes.user_routes.hard_delete_user_me"
    ) as mock_hard:

        r = client.delete(f"{API_PREFIX}/users/me")
        assert r.status_code == 204, r.text

        mock_soft.assert_called_once()
        mock_hard.assert_not_called()
