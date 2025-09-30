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
