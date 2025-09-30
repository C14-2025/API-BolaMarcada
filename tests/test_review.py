# ###
# import pytest
# import uuid
# from fastapi.testclient import TestClient
# from main import app
# from sqlalchemy import create_engine
# from sqlalchemy.orm import sessionmaker
# from core.database import Base
# from models.models import Review

# client = TestClient(app)

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