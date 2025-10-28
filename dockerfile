FROM python:3.12-slim

# Logs previsíveis e sem .pyc
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# build deps + libpq + bash (wait-for-it usa bash)
RUN apt-get update && apt-get install -y \
    bash \
    build-essential \
    libpq-dev \
 && rm -rf /var/lib/apt/lists/*

# Diretório de trabalho (dentro do container; não precisa existir no host)
WORKDIR /app

# deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# código da app (raiz do teu repo)
COPY . .

# wait-for-it (normaliza CRLF e garante execução)
COPY scripts/wait-for-it.sh /wait-for-it.sh
RUN chmod +x /wait-for-it.sh && sed -i 's/\r$//' /wait-for-it.sh

# Wrapper de inicialização: espera DB -> alembic (opcional) -> fallback create_all() -> uvicorn
RUN set -eux; \
  cat > /app/docker-entrypoint.sh <<'SH' && chmod +x /app/docker-entrypoint.sh && sed -i 's/\r$//' /app/docker-entrypoint.sh
#!/usr/bin/env bash
set -euo pipefail

HOST="${POSTGRES_HOST:-${POSTGRES_SERVER:-}}"
PORT="${POSTGRES_PORT:-5432}"

if [[ -n "${HOST}" ]]; then
  echo "[entrypoint] aguardando Postgres em ${HOST}:${PORT}..."
  /wait-for-it.sh "${HOST}:${PORT}" -t 60 -- echo "[entrypoint] Postgres OK"
else
  echo "[entrypoint] POSTGRES_HOST/POSTGRES_SERVER não definido — pulando wait."
fi

# 1) Alembic se houver ini + pacote instalado
if [[ -f "alembic.ini" ]]; then
  if python - 2>/dev/null <<'PY'
import importlib, sys
try:
    importlib.import_module("alembic")
except Exception:
    sys.exit(1)
PY
  then
    echo "[entrypoint] alembic upgrade head ..."
    alembic upgrade head || echo "[entrypoint][WARN] alembic falhou; seguindo mesmo assim."
  else
    echo "[entrypoint] alembic não instalado — pulando."
  fi
else
  echo "[entrypoint] alembic.ini ausente — pulando Alembic."
fi

# 2) Fallback: tenta Base/engine e cria as tabelas
python - <<'PY' || true
candidates = (
    "database",          # raiz (recomendado criar um fino reexportando Base/engine)
    "app.database",      # projetos que usam pacote app/
    "src.database",      # projetos com src/
)
import importlib
for name in candidates:
    try:
        m = importlib.import_module(name)
        Base = getattr(m, "Base", None)
        engine = getattr(m, "engine", None)
        if Base is not None and engine is not None:
            Base.metadata.create_all(bind=engine)
            print(f"[entrypoint] create_all() executado via {name}")
            break
    except Exception:
        pass
else:
    print("[entrypoint] nenhum Base/engine encontrado para create_all() (ok se Alembic já migrou)")
PY

echo "[entrypoint] iniciando uvicorn ..."
exec uvicorn main:app --host 0.0.0.0 --port 8000
SH

EXPOSE 8000

# Importante: CMD (não ENTRYPOINT) para o Jenkins poder sobrescrever sem efeitos colaterais.
CMD ["/app/docker-entrypoint.sh"]
