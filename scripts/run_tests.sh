#!/bin/sh
set -e

python - <<PY
import socket, time
host = "db"
port = 5432
for attempt in range(120):
    try:
        with socket.create_connection((host, port), timeout=1):
            print("db pronto")
            break
    except Exception:
        print("aguardando db...")
        time.sleep(1)
else:
    raise SystemExit("db nao respondeu")
PY

mkdir -p reports
pytest --junitxml=reports/junit.xml -q