#!/usr/bin/env bash
set -euo pipefail

# 0) Espera DB
/wait-for-it.sh "${POSTGRES_HOST:-db}:${POSTGRES_PORT:-5432}" -t 30 || {
  echo "[entrypoint] DB indisponível"; exit 1;
}

# 1) Prepara env (útil p/ Alembic e SQLAlchemy)
export PYTHONPATH="${PYTHONPATH:-/app}"
export DATABASE_URL="${DATABASE_URL:-postgresql+psycopg2://${POSTGRES_USER:-postgres}:${POSTGRES_PASSWORD:-postgres}@${POSTGRES_HOST:-db}:${POSTGRES_PORT:-5432}/${POSTGRES_DB:-bolamarcadadb}}"

echo "[entrypoint] DATABASE_URL=${DATABASE_URL}"

# 2) Tenta Alembic (se existir). Não falha se não tiver alembic instalado.
if [ -f alembic.ini ]; then
  echo "[entrypoint] Rodando alembic upgrade head..."
  set +e
  alembic upgrade head
  rc=$?
  set -e
  if [ $rc -eq 0 ]; then
    echo "[entrypoint] Alembic OK."
    exec uvicorn main:app --host 0.0.0.0 --port 8000
  else
    echo "[entrypoint] Alembic falhou ($rc). Vou tentar fallback create_all()."
  fi
else
  echo "[entrypoint] Sem alembic.ini; vou tentar fallback create_all()."
fi

# 3) Fallback: procurar Base/engine em arquivos comuns na RAIZ
python - <<'PY'
import os, sys, importlib.util, pathlib
print("[entrypoint] fallback: tentando localizar Base/engine...")
base_dir = pathlib.Path("/app")
candidates = [
    "database.py", "db.py",
    "db/database.py", "core/database.py", "src/db.py",
    "backend/database.py", "backend/db.py",
]
found = False
for rel in candidates:
    p = base_dir / rel
    if p.exists():
        spec = importlib.util.spec_from_file_location("db_auto", str(p))
        mod = importlib.util.module_from_spec(spec)  # type: ignore
        sys.modules["db_auto"] = mod
        spec.loader.exec_module(mod)  # type: ignore
        if hasattr(mod, "Base") and hasattr(mod, "engine"):
            print(f"[entrypoint] usando {rel} (Base/engine)")
            mod.Base.metadata.create_all(bind=mod.engine)
            found = True
            break
if not found:
    print("[entrypoint] Nao encontrei database.py com Base/engine — pulando create_all().")
PY

echo "[entrypoint] iniciando uvicorn..."
exec uvicorn main:app --host 0.0.0.0 --port 8000
