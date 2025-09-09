# ⚽ BOLA MARCADA - Backend

Este é o **backend** do projeto **BOLA MARCADA**, desenvolvido com **FastAPI**.  
O objetivo do sistema é fornecer uma API rápida, segura e escalável para gerenciar os recursos da aplicação.

---

## 🚀 Tecnologias utilizadas
- [Python 3.10+](https://www.python.org/)
- [FastAPI](https://fastapi.tiangolo.com/)
- [Uvicorn](https://www.uvicorn.org/)
- [Pydantic](https://docs.pydantic.dev/)
- [SQLAlchemy](https://www.sqlalchemy.org/)

---

## 📂 Estrutura de diretórios

```bash
backend/
│── main.py       # Ponto de entrada da aplicação FastAPI
│── models.py     # Definição das tabelas do banco (SQLAlchemy)
│── schemas.py    # Validações e contratos de dados (Pydantic)
│── requirements.txt  # Dependências do projeto
```

---

## ⚙️ Como rodar o projeto

1. Clone o repositório:
```bash
git clone https://github.com/seu-usuario/bola-marcada.git
```

2. Crie e ative um ambiente virtual:
```bash
python -m venv .venv
source .venv/bin/activate   # Linux/Mac
.venv\Scripts\activate      # Windows
```

3. Instale as dependências:
```bash
pip install -r requirements.txt
```

4. Execute a aplicação:
```bash
uvicorn main:app --reload
```

###### O servidor estará rodando em: http://127.0.0.1:8000

---

## 📖 Documentação automática
### O FastAPI gera documentação interativa para a API:
- Swagger UI: http://127.0.0.1:8000/docs
- Redoc: http://127.0.0.1:8000/redoc
