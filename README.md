# BOLA MARCADA – Backend

API desenvolvida com **FastAPI**, focada em simplicidade, velocidade e organização.  
O sistema gerencia contas de usuários, centros esportivos, campos e horários disponíveis para reservas.

## Instalação

1. Clone o repositório:
```bash
git clone https://github.com/seu-usuario/bola-marcada.git
```

2. Crie e ative o ambiente virtual:
```bash
python -m venv .venv
source .venv/bin/activate   # Mac/Linux
.venv\Scripts\activate      # Windows
```

3. Instale as dependências:
```bash
pip install -r requirements.txt
```


## Executando o Projeto

Rode o servidor FastAPI:
```bash
python main.py
```

Servidor disponível em:
**http://localhost:8000**

Documentação automática:
- Swagger: **http://localhost:8000/docs**
- Redoc: **http://localhost:8000/redoc**


## Testes

Execute todos os testes com:
```bash
pytest
```


## Funcionalidades do BOLA MARCADA

### CRUD de Conta
- Criar conta  
- Login  
- Atualizar informações  
- Excluir conta  

### CRUD de Centros Esportivos
- Cadastrados usando **CNPJ**
- Localização
- Preço por hora
- Um centro esportivo pode ter **vários campos**
- Edição e exclusão de centros esportivos

### CRUD de Campos
- Associados a um centro esportivo
- Fotos do campo
- Tipos suportados:
  - Futebol  
  - Basquete  
  - Vôlei  
  - Futsal  
  - Outros

### Marcação de Horários
- Usuário pode ver horários disponíveis
- Criar reserva
- Cancelar reserva
- Evita conflitos de agendamento


## Estrutura do Projeto

```
backend/
│── main.py                           # Entrada da aplicação
│── models/                           # Modelos do banco
│      │── models.py
│      └── models.py
│
│── routes/                           # Endpoints organizados
│      │── availability_routes.py
│      │── booking_routes.py
│      │── field_routes.py
│      │── review_routes.py
│      │── sports_center_routes.py
│      └── user_routes.py
│
│── schemas/                          # Schemas Pydantic
│      │── availability_schemas.py
│      │── booking_schemas.py
│      │── field_schemas.py
│      │── review_schemas.py
│      │── sports_center_schemas.py
│      └── user_schemas.py
│
│── scripts/                          # Script para enviar e-mail
│      └── shell.sh
│
│── services/                         # Comunicação com BD
│      │── availability_service.py
│      │── booking_service.py
│      │── field_service.py
│      │── review_service.py
│      │── sports_center_service.py
│      └── user_service.py
│
│── tests/                            # Testes Pytest
│      │── auth_test.py
│      │── conftest.py
│      │── field_test.py
│      │── test_review.py
│      │── test_sports_center.py
│      └── tests_utils.py
│
│── utils/                            # Utilidades
│      │── security.py
│      └── validators.py
│
└── requirements.txt                  # Dependências
```