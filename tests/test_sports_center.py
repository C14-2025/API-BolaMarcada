from fastapi.testclient import TestClient
from unittest.mock import patch
import random
from main import app

client = TestClient(app)

API_PREFIX = "/api/v1"
SPORTS_CENTER_ROUTE = f"{API_PREFIX}/sports_center"


# Teste de criação de sports center
def test_create_sports_center():
    payload = {
        "user_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
        "name": "Centro Teste",
        "cnpj": str(random.randint(10000000000000, 99999999999999)),
        "latitude": -23.561684,
        "longitude": -46.655981,
        "photo_path": None,
        "description": "Campo de futebol teste",
    }

    # PATCH no módulo de rotas onde a função é usada
    with patch(
        "routes.sports_center_routes.create_sports_center_service"
    ) as mock_service:
        mock_service.return_value = 1
        response = client.post(f"{SPORTS_CENTER_ROUTE}/create", json=payload)

    assert response.status_code == 201
    data = response.json()
    assert data["message"] == "Centro esportivo criado com sucesso."
    assert data["id"] == 1


# Teste de GET de sports center por ID
def test_get_sports_center():
    mock_center = {
        "id": 1,
        "user_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
        "name": "Centro Teste",
        "cnpj": str(random.randint(10000000000000, 99999999999999)),
        "latitude": -23.561684,
        "longitude": -46.655981,
        "photo_path": None,
        "description": "Outro campo de teste",
    }

    with patch(
        "routes.sports_center_routes.get_sports_center_by_id_service"
    ) as mock_service:
        mock_service.return_value = mock_center
        response = client.get(f"{SPORTS_CENTER_ROUTE}/1")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 1
    assert data["name"] == mock_center["name"]


# Teste de deletar sports center existente
def test_delete_sports_center():
    with patch(
        "routes.sports_center_routes.delete_sports_center_by_id"
    ) as mock_service:
        mock_service.return_value = None
        response = client.delete(f"{SPORTS_CENTER_ROUTE}/1")

    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Centro esportivo deletado com sucesso."


# Teste de criação de sports center com CNPJ duplicado (409)
def test_duplicate_cnpj():
    payload = {
        "user_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
        "name": "Centro Duplicado",
        "cnpj": str(random.randint(10000000000000, 99999999999999)),
        "latitude": -23.561684,
        "longitude": -46.655981,
        "photo_path": None,
        "description": "Primeiro centro",
    }

    with patch(
        "routes.sports_center_routes.create_sports_center_service"
    ) as mock_service:
        mock_service.side_effect = ValueError("CNPJ já cadastrado")
        response = client.post(f"{SPORTS_CENTER_ROUTE}/create", json=payload)

    assert response.status_code == 409
    assert response.json()["detail"] == "CNPJ já cadastrado"


# Teste de campos obrigatórios ausentes
def test_missing_required_fields():
    response = client.post(
        f"{SPORTS_CENTER_ROUTE}/create",
        json={"latitude": -23.561684, "longitude": -46.655981},
    )
    assert response.status_code == 422


# Teste de GET de sports center inexistente (404)
def test_get_nonexistent_sports_center():
    fake_id = random.randint(1000, 9999)
    with patch(
        "routes.sports_center_routes.get_sports_center_by_id_service"
    ) as mock_service:
        mock_service.return_value = None
        response = client.get(f"{SPORTS_CENTER_ROUTE}/{fake_id}")

    assert response.status_code == 404
    assert response.json()["detail"] == "Centro esportivo não encontrado."
