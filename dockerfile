FROM python:3.13-slim

RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

# usa ENTRYPOINT/CMD em forma exec para previsibilidade
ENTRYPOINT ["sh", "-c"]
CMD ["alembic upgrade head && uvicorn main:app --host 0.0.0.0 --port 8000"]
