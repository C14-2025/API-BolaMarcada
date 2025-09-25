# tests/testutils.py
import uuid
from types import SimpleNamespace
from importlib import import_module
from unittest.mock import MagicMock
from fastapi import FastAPI
from fastapi.testclient import TestClient

def make_client(
    routes_module: str = "routes.user_routes",  # ajuste se o caminho for outro
    api_prefix: str = "/api/v1",
) -> TestClient:
    ur = import_module(routes_module)
    user_router = getattr(ur, "user_router")
    get_db = getattr(ur, "get_db")
    get_current_user = getattr(ur, "get_current_user")

    app = FastAPI()
    app.include_router(user_router, prefix=api_prefix)

    # DB mock (não usamos de verdade porque patchamos os services)
    def _override_get_db():
        yield MagicMock()

    # Usuário autenticado "realista" para não quebrar validadores (cpf string de 11 dígitos)
    def _override_get_current_user():
        return SimpleNamespace(
            id=uuid.uuid4(),
            is_active=True,
            name="Auth User",
            email="auth@example.com",
            phone=None,
            avatar=None,
            cpf="12345678901",
        )

    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[get_current_user] = _override_get_current_user

    return TestClient(app)
