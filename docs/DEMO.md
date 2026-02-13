# Demo

This demo shows the core Auth Service flows:
- JWT (RS256) + JWKS
- Access / Refresh tokens
- Role-based access control (RBAC)

## Prerequisites
- Docker + Docker Compose
- Make

## 0) Configure environment

```bash
cp .env.example .env
```

> Note: `.env` is used only for local development.

## 1) Start the stack

```bash
make up
make health
```

Open Swagger UI:

* [http://localhost:8000/docs](http://localhost:8000/docs)

## 2) Bootstrap database (explicit, no magic)

```bash
make migrate
make seed-roles
```

(Optional) Create an admin/superuser (requires `SUPERUSER_PASSWORD`):

```bash
make create-superuser
```

## 3) JWKS: verify public keys are exposed

```bash
curl -s http://localhost:8000/.well-known/jwks.json | head
```

Expected: JSON with `keys: [...]`.

## 4) Auth: login and get tokens

### 4.1 Register a user (if supported)

```bash
curl -s -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"demo@example.com","password":"DemoPass123!"}'
```

### 4.2 Login (access + refresh)

```bash
TOKENS=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"demo@example.com","password":"DemoPass123!"}')

echo "$TOKENS"
```

Extract tokens (jq required, optional):

```bash
ACCESS=$(echo "$TOKENS" | jq -r '.access_token')
REFRESH=$(echo "$TOKENS" | jq -r '.refresh_token')
```

If you don’t have jq, just copy tokens from the response manually.

## 5) Refresh flow

```bash
curl -s -X POST http://localhost:8000/api/v1/auth/refresh \
  -H "Content-Type: application/json" \
  -d "{\"refresh_token\":\"$REFRESH\"}"
```

Expected: new `access_token`.

## 6) RBAC: verify role-protected endpoint

Call a protected endpoint (replace the URL with a real RBAC-protected endpoint):

```bash
curl -i http://localhost:8000/api/v1/admin/ping \
  -H "Authorization: Bearer $ACCESS"
```

Expected:

* `403` for a normal user
* `200` after granting the required role (or using a superuser token)

## 7) Shutdown

```bash
make down
```