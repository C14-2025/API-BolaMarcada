from fastapi.testclient import TestClient
from unittest.mock import patch
import random

from main import app

client = TestClient(app)

API_PREFIX = "/api/v1"
SPORTS_CENTER_ROUTE = f"{API_PREFIX}/sports_center"


def test_create_sports_center():
    payload = {
        "user_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
        "name": "Centro Teste",
        "cnpj": "12345678000103",
        "latitude": -23.561684,
        "longitude": -46.655981,
        "photo_path": None,
        "description": "Campo de futebol teste",
    }

    with patch("routes.sports_center_routes.create_sports_center") as mock_service:
        mock_service.return_value = 1
        response = client.post(f"{SPORTS_CENTER_ROUTE}/create", json=payload)

        assert response.status_code == 201
        data = response.json()
        assert response.json()["message"] == "Centro esportivo criado com sucesso."
        assert data["id"] == 1


def test_get_sports_center():
    payload = {
        "id": 1,
        "user_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
        "name": "Centro Teste",
        "cnpj": "11122233344455",
        "latitude": -23.561684,
        "longitude": -46.655981,
        "photo_path": None,
        "description": "Outro campo de teste",
    }
    with patch("routes.sports_center_routes.get_sports_center") as mock_service:

        mock_service.return_value = payload
        response = client.get(f"{SPORTS_CENTER_ROUTE}/1")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 1


def test_delete_sports_center():
    with patch("routes.sports_center_routes.delete_sports_center") as mock_service:
        mock_service.return_value = None
        response = client.delete(f"{SPORTS_CENTER_ROUTE}/1")

    assert response.status_code == 200
    data = response.json()
    assert data.json()["message"] == "Centro esportivo deletado com sucesso."


def test_duplicate_cnpj():
    with patch("routes.sports_center_routes.create_sports_center") as mock_service:
        json_data = {
            "name": "Centro Duplicado",
            "user_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
            "cnpj": "12345678000103",
            "latitude": -23.561684,
            "longitude": -46.655981,
            "photo_path": None,
            "description": "Primeiro centro",
        }
        mock_service.side_effect = ValueError("CNPJ já cadastrado")
        response = client.post(f"{SPORTS_CENTER_ROUTE}/create", json=json_data)
        assert response.status_code == 409
        assert response.json()["detail"] == "CNPJ já cadastrado"


def test_missing_required_fields():
    response = client.post(
        f"{SPORTS_CENTER_ROUTE}/create",
        json={"latitude": -23.561684, "longitude": -46.655981},
    )
    assert response.status_code == 422


def test_get_nonexistent_sports_center():
    with patch(
        "services.sports_center_service.get_sports_center_by_id_service"
    ) as mock_service:
        mock_service.return_value = None
        fake_id = random.randint(1, 10000)
        response = client.get(f"{SPORTS_CENTER_ROUTE}/{fake_id}")
        assert response.status_code == 404
        assert response.json()["detail"] == "Centro esportivo não encontrado."
