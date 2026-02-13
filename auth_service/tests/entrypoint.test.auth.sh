#!/usr/bin/env bash
set -euo pipefail

export JWT_PRIVATE_KEY_PATH="${JWT_PRIVATE_KEY_PATH:-/app/keys/jwtRS256.key}"
export JWT_PUBLIC_KEY_PATH="${JWT_PUBLIC_KEY_PATH:-/app/keys/jwtRS256.key.pub}"

mkdir -p /app/keys
if [ ! -f /app/keys/jwtRS256.key ]; then
  echo "Generating JWT keys for tests..."
  openssl genrsa -out /app/keys/jwtRS256.key 2048
  openssl rsa -in /app/keys/jwtRS256.key -pubout -out /app/keys/jwtRS256.key.pub
fi

echo "[test-entrypoint] Waiting for Postgres..."
until pg_isready -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}"; do
  sleep 1
done
echo "[test-entrypoint] Postgres is ready"

echo "[test-entrypoint] Waiting for Redis..."
python - <<'PY'
import os, socket, time
host = os.environ.get("REDIS_HOST", "localhost")
port = int(os.environ.get("REDIS_PORT", "6379"))
deadline = time.time() + 60
while time.time() < deadline:
    try:
        with socket.create_connection((host, port), timeout=1):
            print("[test-entrypoint] Redis port is open")
            break
    except OSError:
        time.sleep(1)
else:
    raise SystemExit("[test-entrypoint] Redis is not ready in time")
PY

exec "$@"
