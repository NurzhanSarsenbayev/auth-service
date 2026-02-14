#!/usr/bin/env bash
set -euo pipefail

# NOTE: demo should use Makefile helpers (single source of truth).
DEMO_DIR=".demo"
AUTH_URL="${AUTH_URL:-http://localhost:8000}"
API="${AUTH_URL}/api/v1"
JWKS_URL="${AUTH_URL}/.well-known/jwks.json"

# --- helpers ---
need_cmd() { command -v "$1" >/dev/null 2>&1 || { echo "FAIL: missing command: $1"; exit 1; }; }

py() {
  if command -v python >/dev/null 2>&1; then python "$@"; return; fi
  if command -v python3 >/dev/null 2>&1; then python3 "$@"; return; fi
  echo "FAIL: python/python3 not found (needed to parse JSON)"; exit 1
}

http_code() {
  # usage: http_code <method> <url> [curl args...]
  local method="$1"; shift
  local url="$1"; shift
  curl -sS -o /dev/null -w "%{http_code}" -X "$method" "$url" "$@"
}

json_get_access() {
  # usage: json_get_access <file>
  local f="$1"
  py - <<PY
import json
with open("$f", "r", encoding="utf-8") as fp:
    data = json.load(fp)
print(data["access_token"])
PY
}

# --- preflight ---
need_cmd docker
need_cmd curl
need_cmd openssl
need_cmd make

if [[ -z "${SUPERUSER_PASSWORD:-}" ]]; then
  echo "FAIL: SUPERUSER_PASSWORD is not set."
  echo "Example (Git Bash): export SUPERUSER_PASSWORD='StrongPass123!'"
  exit 1
fi

mkdir -p "${DEMO_DIR}"

echo "==> 1) Ensure env file"
make init-env >/dev/null

echo "==> 2) Ensure JWT keys"
if [[ ! -f "auth_service/keys/jwtRS256.key" || ! -f "auth_service/keys/jwtRS256.key.pub" ]]; then
  openssl genrsa -out auth_service/keys/jwtRS256.key 2048
  openssl rsa -in auth_service/keys/jwtRS256.key -pubout -out auth_service/keys/jwtRS256.key.pub
  echo "OK: keys generated"
else
  echo "OK: keys already exist"
fi

echo "==> 3) Start stack + wait for health/ready"
make up >/dev/null

echo "==> 3a) Wait for healthz (via make health)"
make health >/dev/null

echo "==> 3b) Wait for readyz (via make ready)"
make ready >/dev/null

echo "==> 4) Explicit bootstrap (migrate, seed roles, superuser)"
make migrate >/dev/null
make seed-roles >/dev/null
make create-superuser SUPERUSER_PASSWORD="${SUPERUSER_PASSWORD}" >/dev/null

echo "==> 5) JWKS reachable"
curl -sS "${JWKS_URL}" | head -c 120 >/dev/null
echo "OK: jwks"

echo "==> 6) Signup demo user"
curl -sS -X POST "${API}/users/signup" \
  -H "Content-Type: application/json" \
  -d '{"username":"demo","email":"demo@example.com","password":"DemoPass123!"}' \
  >/dev/null || true
echo "OK: signup (or already exists)"

echo "==> 7) Login demo user"
curl -sS -X POST "${API}/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=demo&password=DemoPass123!" \
  -c "${DEMO_DIR}/cookies_demo.txt" > "${DEMO_DIR}/tokens_demo.json"

ACCESS_DEMO="$(json_get_access "${DEMO_DIR}/tokens_demo.json")"

echo "==> 8) RBAC check (demo user must be 403)"
CODE="$(http_code POST "${API}/roles/create" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${ACCESS_DEMO}" \
  -d '{"name":"test_role","description":"demo role"}')"

if [[ "${CODE}" != "403" ]]; then
  echo "FAIL: expected 403 for demo user, got ${CODE}"
  exit 1
fi
echo "OK: demo user forbidden (403)"

echo "==> 9) Login admin"
curl -sS -X POST "${API}/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=${SUPERUSER_PASSWORD}" \
  -c "${DEMO_DIR}/cookies_admin.txt" > "${DEMO_DIR}/tokens_admin.json"

ACCESS_ADMIN="$(json_get_access "${DEMO_DIR}/tokens_admin.json")"

echo "==> 10) RBAC check (admin must be 201)"
CODE="$(http_code POST "${API}/roles/create" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${ACCESS_ADMIN}" \
  -d '{"name":"editor","description":"demo role"}')"

if [[ "${CODE}" != "201" && "${CODE}" != "409" ]]; then
  # 409 is acceptable if role already exists from a previous run
  echo "FAIL: expected 201 (or 409 if exists) for admin, got ${CODE}"
  exit 1
fi
echo "OK: admin allowed (${CODE})"

echo "==> 11) Refresh flow (cookie-based, must be 200)"
CODE="$(http_code POST "${API}/auth/refresh" -b "${DEMO_DIR}/cookies_admin.txt")"
if [[ "${CODE}" != "200" ]]; then
  echo "FAIL: expected 200 for refresh, got ${CODE}"
  exit 1
fi
echo "OK: refresh (200)"

echo
echo "SUCCESS"
echo "Swagger UI: ${AUTH_URL}/docs"
echo "JWKS:      ${JWKS_URL}"
echo "Artifacts: ${DEMO_DIR}/"
