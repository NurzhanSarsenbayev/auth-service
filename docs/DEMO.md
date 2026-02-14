# Demo

## What this demo proves

- Tokens are signed with RS256 and can be verified via JWKS.
- Refresh tokens are stored and can be revoked (logout / blacklist).
- - Health and readiness probes behave correctly (readyz returns 503 when Redis/Postgres are down).
- RBAC is enforced server-side (403 vs 201 behavior is demonstrated).
- Startup is explicit: migrations/roles/superuser are not “magic”.
- The system is reproducible via `make demo`.

---

## Prerequisites

- Docker + Docker Compose
- Make
- curl
- OpenSSL
- (optional) jq

---
## Quickstart (automated)

Run the full demo:

```bash
export SUPERUSER_PASSWORD=StrongPass123!
make demo
```
Cleanup:

```bash
make demo-clean
```
Everything below is the manual, step-by-step version.

---

## 0) Environment setup

Initialize environment:

```bash
make init-env
````

Edit:

```
auth_service/.env.auth
```

Set a strong password:

```
SUPERUSER_PASSWORD=StrongPass123!
```

Export it for demo commands (Git Bash):

```bash
export SUPERUSER_PASSWORD=StrongPass123!
```

---

## 1) Generate JWT keys

Run from repository root:

```bash
openssl genrsa -out auth_service/keys/jwtRS256.key 2048
openssl rsa -in auth_service/keys/jwtRS256.key -pubout -out auth_service/keys/jwtRS256.key.pub
```

> Keys are local-only and ignored by git.

---

## 2) Start the stack

```bash
make up
make health
```

Swagger UI:

```
http://localhost:8000/docs
```

---

## 3) Explicit bootstrap

```bash
make migrate
make seed-roles
make create-superuser SUPERUSER_PASSWORD=$SUPERUSER_PASSWORD
```

This creates:

* admin user
* role: admin
* password: value of SUPERUSER_PASSWORD

---

## 4) JWKS verification

```bash
curl -s http://localhost:8000/.well-known/jwks.json | head
```

Expected: JSON containing RSA public key metadata.

---

## 5) Prepare demo workspace

Create isolated folder for demo artifacts:

```bash
mkdir -p .demo
```

All temporary files will be stored in `.demo/`.

---

## 6) Create regular user

```bash
curl -s -X POST http://localhost:8000/api/v1/users/signup \
  -H "Content-Type: application/json" \
  -d '{"username":"demo","email":"demo@example.com","password":"DemoPass123!"}'
```

---

## 7) Login as regular user

```bash
curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=demo&password=DemoPass123!" \
  -c .demo/cookies_demo.txt > .demo/tokens_demo.json
```

Extract access token (optional, requires jq):

```bash
ACCESS_DEMO=$(cat .demo/tokens_demo.json | jq -r '.access_token')
```

---

## 8) RBAC test (should fail for regular user)

```bash
curl -i -X POST http://localhost:8000/api/v1/roles/create \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ACCESS_DEMO" \
  -d '{"name":"test_role","description":"demo role"}'
```

Expected: `403 Forbidden`

---

## 9) Login as admin

```bash
curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=$SUPERUSER_PASSWORD" \
  -c .demo/cookies_admin.txt > .demo/tokens_admin.json
```

Extract admin access token:

```bash
ACCESS_ADMIN=$(cat .demo/tokens_admin.json | jq -r '.access_token')
```

---

## 10) RBAC test (admin should succeed)

```bash
curl -i -X POST http://localhost:8000/api/v1/roles/create \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ACCESS_ADMIN" \
  -d '{"name":"editor","description":"demo role"}'
```

Expected: `201 Created`

---

## 11) Refresh flow (cookie-based)

```bash
curl -s -X POST http://localhost:8000/api/v1/auth/refresh \
  -b .demo/cookies_admin.txt
```

Expected: new access token.

---

## 12) Cleanup

Stop containers:

```bash
make down
```

Remove demo artifacts:

```bash
rm -rf .demo
```

---

## Notes

* Demo artifacts are stored in `.demo/` and ignored by git.
* No automatic migrations or seed operations happen on container startup.
* JWT keys are mounted into the container via Docker volume.
