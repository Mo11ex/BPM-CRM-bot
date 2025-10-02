#!/usr/bin/env bash
set -e

HOST="${DATABASE_HOST:-postgres}"
PORT="${DATABASE_PORT:-5432}"
RETRIES=60
SLEEP_SECONDS=1

echo "Waiting for Postgres at ${HOST}:${PORT} ..."

i=0
while [ $i -lt $RETRIES ]; do
  # Попробуем соединиться питоном (на случай, если nc нет)
  python - <<PY >/dev/null 2>&1 || true
import socket, os, sys
host = os.getenv('DATABASE_HOST','${HOST}')
port = int(os.getenv('DATABASE_PORT','${PORT}'))
try:
    s = socket.create_connection((host, port), timeout=2)
    s.close()
    sys.exit(0)
except Exception:
    sys.exit(1)
PY
  if [ $? -eq 0 ]; then
    echo "Postgres is available."
    exec "$@"
  fi
  i=$((i+1))
  echo "Postgres not ready yet ($i/${RETRIES}) - waiting ${SLEEP_SECONDS}s..."
  sleep ${SLEEP_SECONDS}
done

echo "Timed out waiting for Postgres at ${HOST}:${PORT}"
exit 1