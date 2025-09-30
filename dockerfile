# Imagem base do Python
FROM python:3.13-slim

# Instala dependências do sistema (postgres + build)
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Define diretório de trabalho
WORKDIR /app

# Copia requirements primeiro para cache de dependências
COPY requirements.txt .

# Instala dependências
RUN pip install --no-cache-dir -r requirements.txt

# Copia todo o projeto
COPY . .

# Expõe a porta da API
EXPOSE 8000

# Comando para rodar migrations automáticas + iniciar API
CMD alembic upgrade head && uvicorn main:app --host 0.0.0.0 --port 8000
