# Auth Service (JWT + RBAC + OAuth)
![CI](https://github.com/NurzhanSarsenbayev/auth-service/actions/workflows/ci.yml/badge.svg?branch=main)

A production-minded authentication and authorization service built with FastAPI.

**One-command demo:**

```bash
make demo
```
This project demonstrates:
- **RS256 JWT** + **JWKS**
- **Refresh** token revocation
- **RBAC** enforcement
- **OAuth** integration
- **Redis**-backed rate limiting
- **CI quality** gate with coverage
- Designed as a **portfolio-grade** backend service.

---

## Implemented Features

### Authentication
- Access & Refresh tokens (RS256)
- Secure HTTP-only refresh cookie
- Token blacklist (Redis)
- Logout (single token / all tokens)

### Authorization
- RBAC with role assignment
- Protected endpoints with role enforcement

### OAuth
- Google OAuth
- Yandex OAuth
- Deterministic fallback username generation

> OAuth providers require environment configuration.

### Observability
- Structured logging
- OpenTelemetry tracing (optional via environment)
- Health endpoint

---

## Architecture Overview

```

```
            +--------------------+
            |    Client / API    |
            +----------+---------+
                       |
                       v
            +--------------------+
            |     FastAPI App    |
            |--------------------|
            | Routers            |
            | Services           |
            | Repositories       |
            +----------+---------+
                       |
    +------------------+------------------+
    |                                     |
    v                                     v
```

+-------------------+               +-------------------+
|    PostgreSQL     |               |      Redis        |
|-------------------|               |-------------------|
| Users             |               | Rate limiting     |
| Roles             |               | Token blacklist   |
| Login history     |               +-------------------+
+-------------------+

JWT signing keys are mounted via volume.
Public keys are exposed via JWKS endpoint.

````

### Trust Boundaries

- JWT private key is never committed.
- Refresh tokens are revocable via Redis blacklist.
- Proxy headers must only be trusted behind a secure reverse proxy.
- See `docs/SECURITY.md` for threat model and limitations.

---

## Quickstart (Reproducible Demo)

The recommended way to run the service:

```bash
make demo
````

This will:

* Generate local JWT keys
* Start PostgreSQL and Redis
* Run migrations
* Seed roles
* Create a superuser (if configured)
* Perform signup / login
* Demonstrate RBAC enforcement
* Demonstrate refresh flow
* Output `DEMO SUCCESS`

Clean up afterwards:

```bash
make demo-clean
```

Full demo explanation: `docs/DEMO.md`

---

## Manual Operations

Initialize environment:

```bash
make init-env
```

Start services:

```bash
make up
```

Run migrations:

```bash
make migrate
```

Seed roles:

```bash
make seed-roles
```

Stop services:

```bash
make down
```

Operational notes: `docs/OPERATIONS.md`

---

## Configuration Model

Environment variables are loaded from `.env.auth`.

Important categories:

* Database connection
* Redis connection
* JWT key paths
* OAuth credentials
* Cookie security flags
* Rate limiting configuration
* Tracing enablement

JWT keys must be mounted via:

```
auth_service/keys/
```

If keys are missing, the application fails fast at startup.

---

## Security Model

This repository includes a detailed security narrative:

See:

```
docs/SECURITY.md
```

It covers:

* Threat model
* Token lifecycle
* CSRF considerations
* Rate limiting assumptions
* What is intentionally not implemented

---

## Quality & CI

CI includes:

* Ruff (lint + format check)
* MyPy (type checking subset)
* Pre-commit hooks
* Pytest with coverage
* Coverage threshold enforcement

Python versions tested:

* 3.11
* 3.12

The CI is designed to reflect the actual project state.
No undocumented behavior.

---

## Roadmap (Honest & Short)

* JSON structured logging output option
* Optional Redis-less mode
* Stronger rate limit key normalization
* Expanded integration tests for OAuth flows

---

## Project Structure

```
auth_service/
    src/
        core/
        services/
        repositories/
        models/
        middleware/
        schemas/
        utils/
    alembic/
    tests/
docs/
Makefile
docker-compose.yml
```

---

## License

For demonstration and portfolio purposes.
