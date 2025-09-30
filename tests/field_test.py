import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
from main import app

client = TestClient(app)

API_PREFIX = "/api/v1"
FIELD_ROUTE = f"{API_PREFIX}/field"

# Teste de criação de campo com sucesso (201)
def test_create_field_success():
    payload = {
        "sports_center_id": 1,
        "name": "Campo Teste",
        "field_type": "soccer",
        "price_per_hour": 100.0,
        "photo_path": "campo_teste.png",
        "description": "Descrição do campo teste"
    }

    # Patch no módulo correto onde a função é usada
    with patch("routes.field_routes.create_field_service") as mock_service:
        mock_service.return_value = 1
        response = client.post(f"{FIELD_ROUTE}/create", json=payload)

    assert response.status_code == 201
    data = response.json()
    assert data["message"] == "Campo criado com sucesso."
    assert data["id"] == 1

# teste de obtenção de campo por ID com sucesso (200)
def test_get_field_success():
    mock_field = {
        "id": 1,
        "sports_center_id": 1,
        "name": "Campo Teste",
        "description": "Descrição do campo teste",
        "capacity": 10,
        "field_type": "soccer",
        "price_per_hour": 100.0,
        "photo_path": "campo_teste.png"
    }

    with patch("routes.field_routes.get_field_by_id") as mock_service:
        mock_service.return_value = mock_field
        response = client.get(f"{FIELD_ROUTE}/1")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 1
    assert data["name"] == "Campo Teste"


# teste de deletar o campo com sucesso (200)
def test_delete_field_success():
    with patch("routes.field_routes.delete_field_by_id") as mock_service:
        mock_service.return_value = None
        response = client.delete(f"{FIELD_ROUTE}/1")

    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Campo deletado com sucesso."


# teste de criar campo existente (409)
def test_create_field_conflict():
    payload = {
        "sports_center_id": 1,
        "name": "Campo Teste",
        "field_type": "soccer",
        "price_per_hour": 100.0,
        "photo_path": "campo_teste.png",
        "description": "Descrição do campo teste"
    }

    # Simula ValueError como se o campo já existisse
    with patch("routes.field_routes.create_field_service") as mock_service:
        mock_service.side_effect = ValueError("Campo já existe")
        response = client.post(f"{FIELD_ROUTE}/create", json=payload)

    assert response.status_code == 409
    data = response.json()
    assert data["detail"] == "Campo já existe"


# teste de busca de campo inexistente (404)
def test_get_field_not_found():
    with patch("routes.field_routes.get_field_by_id") as mock_service:
        mock_service.return_value = None
        response = client.get(f"{FIELD_ROUTE}/999")  # ID inexistente

    assert response.status_code == 404
    data = response.json()
    assert data["detail"] == "Campo não encontrado."


# Teste de deletar campo inexistente (404)
def test_delete_field_not_found():
    with patch("routes.field_routes.delete_field_by_id") as mock_service:
        mock_service.side_effect = ValueError("Campo não encontrado")
        response = client.delete(f"{FIELD_ROUTE}/999")

    assert response.status_code == 404
    data = response.json()
    # Corrigido: remove o ponto final
    assert data["detail"] == "Campo não encontrado"