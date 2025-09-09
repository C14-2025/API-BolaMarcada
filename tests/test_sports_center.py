from tests.conftest import client
import random


# Teste de criação de sports center
def test_create_sports_center(client):
    response = client.post(
        "/sports_center/create",
        json={
            "name": "Centro Teste",
            "cnpj": str(random.randint(0, 100000)),
            "latitude": -23.561684,
            "longitude": -46.655981,
            "photo_path": None,
            "description": "Campo de futebol teste",
        },
    )
    assert response.status_code == 201
    assert "id" in response.json()
    assert response.json()["message"] == "Centro esportivo criado com sucesso."


# Teste de GET por ID
def test_get_sports_center(client):
    create_resp = client.post(
        "/sports_center/create",
        json={
            "name": "Centro Teste 2",
            "cnpj": str(random.randint(0, 100000)),
            "latitude": -23.561684,
            "longitude": -46.655981,
            "photo_path": None,
            "description": "Outro campo de teste",
        },
    )
    sports_center_id = create_resp.json()["id"]

    response = client.get(f"/sports_center/{sports_center_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == sports_center_id
    assert data["name"] == "Centro Teste 2"


# Teste de DELETE
def test_delete_sports_center(client):
    create_resp = client.post(
        "/sports_center/create",
        json={
            "name": "Centro Teste 3",
            "cnpj": "12345678000102",
            "latitude": -23.561684,
            "longitude": -46.655981,
            "photo_path": None,
            "description": "Campo para deletar",
        },
    )
    sc_id = create_resp.json()["id"]

    delete_resp = client.delete(f"/sports_center/{sc_id}")
    assert delete_resp.status_code == 200
    assert delete_resp.json()["message"] == "Centro esportivo deletado com sucesso."

    get_resp = client.get(f"/sports_center/{sc_id}")
    assert get_resp.status_code == 404


# Teste de duplicidade de CNPJ
def test_duplicate_cnpj(client):
    json_data = {
        "name": "Centro Duplicado",
        "cnpj": "12345678000103",
        "latitude": -23.561684,
        "longitude": -46.655981,
        "photo_path": None,
        "description": "Primeiro centro",
    }
    client.post("/sports_center/create", json=json_data)
    response = client.post("/sports_center/create", json=json_data)
    assert response.status_code == 409
    assert response.json()["detail"] == "CNPJ já cadastrado"


# Teste de campos obrigatórios ausentes
def test_missing_required_fields(client):
    response = client.post("/sports_center/create", json={"latitude": -23.561684, "longitude": -46.655981})
    assert response.status_code == 422


# Teste de GET de centro inexistente
def test_get_nonexistent_sports_center(client):
    response = client.get("/sports_center/99999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Centro esportivo não encontrado."
