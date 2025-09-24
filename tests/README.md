# API Bola Marcada — Entrega de Testes

Resumo da atividade de testes (com pequenas refatorações para estabilizar autenticação e schema).

---

## ⚙️ Stack

- **FastAPI**
- **SQLAlchemy**
- **Alembic**
- **Pydantic v2** (+ pydantic-settings)
- **Pytest** (SQLite em memória nos testes)
- **Passlib/bcrypt** (hash)
- **JWT** em `utils.security`

---

## ✅ O que é testado

### 3 testes unitários

- **test_create_user_hash_password**: Confere geração/validação de hash.
- **test_authenticate_invalid_password**: `authenticate` falha com senha incorreta.
- **test_create_and_decode_access_token**: Cria e decodifica o JWT.

### 1 teste de integração

- **test_signin_route_integration**: Cria usuário no DB em memória, faz POST `/users/signin` e valida:
  - Status 200
  - `token_type="bearer"`
  - `access_token` válido

> Os testes usam SQLite em memória via `conftest.py` (cria/dropa tabelas automaticamente).  
> Não precisa de Postgres para rodar os testes.

---

## ▶️ Como rodar

```shell
# Ativar venv (Windows)
.\venv\Scripts\activate

# Instalar dependências
pip install -r requirements.txt

# Rodar a suíte
pytest -v

```
