# ###
# import pytest
# import uuid
# from fastapi.testclient import TestClient
# from unittest.mock import patch
# from main import app

# client = TestClient(app)
# REVIEW_ROUTE = "/review"

# # Configuração do banco de dados de teste
# SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
# engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
# TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# # Criar as tabelas no banco de dados de teste
# Base.metadata.create_all(bind=engine)

# @pytest.fixture(scope="function")
# def test_db():
#     """Fixture para fornecer uma sessão de banco de dados de teste."""
#     session = TestingSessionLocal()
#     try:
#         # Inserir dados necessários para os testes
#         session.add_all([
#             Review(
#                 user_id=uuid.uuid4(), 
#                 sports_center_id=uuid.uuid4(), 
#                 rating=5, 
#                 comment="Ótimo lugar!"
#             ),
#         ])
#         session.commit()
#         yield session
#     finally:
#         session.close()


# # Teste positivo: Criar uma review com sucesso
# @pytest.mark.parametrize("review_data", [
#     {
#         "user_id": str(uuid.uuid4()), 
#         "sports_center_id": str(uuid.uuid4()), 
#         "rating": 5, 
#         "comment": "Ótimo lugar!"
#     },
# ])
# def test_create_review_success(test_db, review_data):
#     response = client.post("/review/create", json=review_data)
#     assert response.status_code == 201
#     assert "id" in response.json()


# # Teste positivo: Buscar uma review existente
# @pytest.mark.parametrize("review_id", [1])
# def test_get_review_success(test_db, review_id):
#     response = client.get(f"/review/{review_id}")
#     assert response.status_code == 200
#     assert response.json()["id"] == review_id


# # Teste negativo: Criar uma review com dados inválidos
# @pytest.mark.parametrize("invalid_data", [
#     {
#         "user_id": str(uuid.uuid4()), 
#         "sports_center_id": str(uuid.uuid4()), 
#         "rating": 6, 
#         "comment": "Nota inválida!"
#     },
# ])
# def test_create_review_failure(test_db, invalid_data):
#     response = client.post("/review/create", json=invalid_data)
#     assert response.status_code == 400


# # Teste negativo: Buscar uma review inexistente
# @pytest.mark.parametrize("nonexistent_review_id", [999])
# def test_get_review_failure(test_db, nonexistent_review_id):
#     response = client.get(f"/review/{nonexistent_review_id}")
#     assert response.status_code == 404
# para comentar inumeras linhas em oython pressione ctrl + k + c
# para descomentar inumeras linhas em oython pressione ctrl + k + u

# tests/test_review.py
import uuid
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
from main import app
from core.database import get_db

API_PREFIX = "/api/v1"                
BASE = f"{API_PREFIX}/review"
client = TestClient(app)

# Evita abrir DB real 
@pytest.fixture(autouse=True)
def _override_db():
    def _fake_db():
        yield None
    app.dependency_overrides[get_db] = _fake_db
    yield
    app.dependency_overrides.pop(get_db, None)

# ========================= TESTES POSITIVOS ===============================

def test_create_review_success():
    """[POS] Cria uma review com sucesso e retorna id + mensagem."""
    payload = {
        "user_id": str(uuid.uuid4()),
        "sports_center_id": 1,
        "rating": 5,
        "comment": "Ótimo lugar!"
    }
    # routes.review_routes importa direto: create_review_service
    with patch("routes.review_routes.create_review_service") as mock_srv:
        mock_srv.return_value = 123
        resp = client.post(f"{BASE}/create", json=payload)

    assert resp.status_code == 201
    data = resp.json()
    assert data["id"] == 123
    assert "Review criada com sucesso." in data["message"]

def test_get_review_success():
    """[POS] Busca uma review existente por ID e retorna 200 com o objeto."""
    fake_review = {
        "id": 1,
        "user_id": str(uuid.uuid4()),
        "sports_center_id": 1,
        "rating": 4,
        "comment": "Bom"
    }
    with patch("routes.review_routes.get_review_by_id") as mock_srv:
        mock_srv.return_value = fake_review
        resp = client.get(f"{BASE}/1")

    assert resp.status_code == 200
    assert resp.json()["id"] == 1

def test_delete_review_success():
    """[POS] Deleta uma review existente e retorna mensagem de sucesso."""
    with patch("routes.review_routes.delete_review_by_id") as mock_del:
        mock_del.return_value = None
        resp = client.delete(f"{BASE}/1")

    assert resp.status_code == 200
    assert resp.json()["message"] == "Review deletada com sucesso."

# ========================= TESTES NEGATIVOS ===============================

def test_get_review_not_found():
    """[NEG] Buscar review inexistente deve retornar 404."""
    with patch("routes.review_routes.get_review_by_id") as mock_srv:
        mock_srv.return_value = None
        resp = client.get(f"{BASE}/999")

    assert resp.status_code == 404
    assert resp.json()["detail"] == "Review não encontrada."

def test_create_review_validation_error():
    """[NEG] Criar review com rating fora do intervalo (1..5) deve retornar 422."""
    payload = {
        "user_id": str(uuid.uuid4()),
        "sports_center_id": 1,
        "rating": 6,        # inválido
        "comment": "Nota inválida"
    }
    resp = client.post(f"{BASE}/create", json=payload)
    assert resp.status_code == 422  # validação Pydantic/FastAPI

def test_delete_review_not_found():
    """[NEG] Excluir review inexistente deve retornar 404."""
    with patch("routes.review_routes.delete_review_by_id") as mock_del:
        mock_del.side_effect = ValueError("Review não encontrada")
        resp = client.delete(f"{BASE}/999")

    assert resp.status_code == 404
    assert resp.json()["detail"] == "Review não encontrada"
