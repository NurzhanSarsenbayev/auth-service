# Auth Service

A production-minded authentication service for issuing and validating JWT tokens (RS256) via JWKS, with refresh tokens,
RBAC, and persistent storage.

This repository is focused on the **Auth Service standalone** path. Other components (if present) are considered
**optional/demo-only**.

---

## Key Features

### Implemented
- JWT (RS256) with JWKS endpoint (public key distribution)
- Access / Refresh token flow
- Role-based access control (RBAC)
- PostgreSQL storage
- Redis (caching / rate limiting depending on configuration)
- Docker Compose standalone setup
- Explicit ops commands (migrations, role seeding, superuser creation) via `make`

### Optional (present but not required for standalone)
- OAuth providers (if enabled/implemented in codebase)
- Tracing / middleware integrations (if enabled)
- Additional services from the original monorepo scope

### Planned
- Strict quality gate: ruff, mypy (runtime strict subset), pre-commit
- Runtime image: **Python 3.11 (Dockerfile)**
- CI test matrix: **3.11 / 3.12** (tests container)
- Reproducible demo script + docs/DEMO.md
- Security narrative: trust boundaries, guarantees, and limitations

---

## 60-second Quickstart (Standalone)

### 1) Configure environment
Copy sample env:
```bash
cp auth_service/.env.auth.sample auth_service/.env.auth
```

### 2) Start services

```bash
make up
make health
```

### 3) Initialize database (explicit)

```bash
make migrate
make seed-roles
```

### 4) Create a superuser (optional)

Superuser is created **only if** `SUPERUSER_PASSWORD` is set in `auth_service/.env.auth`:

```bash
make create-superuser
```

### 5) Open API docs

* [http://localhost:8000/docs](http://localhost:8000/docs)

---

## Operations

Common commands:

```bash
make ps
make logs-auth
make logs-postgres-auth
make logs-redis
make down
```

---

## Documentation

* `docs/ARCHITECTURE.md` - system overview and key flows
* `docs/OPERATIONS.md` - operational guide (runbooks, troubleshooting)
* `docs/SECURITY.md` - key handling, trust boundaries, security notes

---

## Notes

This project aims to be **honest and reproducible**:

* No automatic migrations/seeding on container startup
* No secrets committed to the repository
* One canonical standalone run path
