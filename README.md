# Auth Service (JWT + RBAC + OAuth)
![CI](https://github.com/NurzhanSarsenbayev/auth-service/actions/workflows/ci.yml/badge.svg?branch=main)

An operationally aware authentication service focused on explicit runtime guarantees,
revocable tokens, and infrastructure reproducibility.

It emphasizes predictable startup, clear dependency contracts, and CI-enforced correctness.

## Operational Contract

This service enforces explicit runtime guarantees:

- The service does not start without valid RSA key files (fail-fast).
- Redis is a required runtime dependency (rate limiting + refresh revocation).
- Health (`/api/v1/healthz`) and readiness (`/api/v1/readyz`) are intentionally separated.
- No implicit database seeding or hidden bootstrap logic.
- Superuser creation requires explicit environment configuration.

These constraints are intentional and documented.

---

## Architecture

High-level architecture and operational principles are documented in:

docs/ARCHITECTURE.md

---

## Quickstart (Reproducible Demo)

This demo proves the operational contract: fail-fast keys,
reproducible infra, and enforceable authZ (RBAC) with revocable refresh tokens.

### Demo prerequisites

You must explicitly provide a superuser password (no hidden seed).

**Git Bash:**
```bash
export SUPERUSER_PASSWORD='StrongPass123!'
```

```bash
make demo
```

This will:
- Generate local keys
- Start Postgres + Redis
- Validate health/readiness
- Run migrations and seed roles
- Demonstrate signup/login, RBAC and refresh flow
  * Swagger UI: http://localhost:8000/docs
  * JWKS:      http://localhost:8000/.well-known/jwks.json
  * Artifacts: .demo/ (access token responses + cookies from the demo run)

Clean up afterwards:

```bash
make demo-clean
```

Full demo explanation: `docs/DEMO.md`

---

## Local quality checks (host tooling)

`make check` and `pre-commit` run local developer tools (ruff, mypy, etc.).
Create a virtualenv and install both runtime and dev requirements:

```bash
python -m venv venv
source venv/Scripts/activate  # Windows Git Bash
pip install -r auth_service/requirements.runtime.txt
pip install -r auth_service/requirements.dev.txt

make check
make precommit
```

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
Check probes:

```bash
make health
make ready
```
**healthz** is a liveness-style endpoint (process is up).

**readyz** is a readiness probe (Postgres + Redis reachable). Returns 503 if dependencies are down.

You can also call the endpoints directly: **/api/v1/healthz** and **/api/v1/readyz**

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

For local standalone runs, .env.auth is used as the canonical env file (created via make init-env).
In Docker, the same file is consumed via docker-compose env_file,
so local and CI use the same configuration surface.

Important categories:

* Database connection
* Redis connection
* JWT key paths
* OAuth credentials
* Cookie security flags
* Rate limiting configuration
* Tracing enablement
* Logging format (LOG_FORMAT=text|json)

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

CI reflects the actual project state. No hidden steps or undocumented behavior.

---
## Design Decisions

- **RS256 instead of HS256** -- enables public key distribution via JWKS and avoids symmetric key sharing.
- **Redis-backed revocation** -- decouples token invalidation from primary storage.
- **Fail-fast startup model** -- prevents undefined runtime states.
- **Docker-first development model** -- ensures CI/local parity.

## Non-Goals

This project intentionally does not implement:

- Key rotation strategy
- Multi-tenant isolation
- Distributed horizontal rate limiting
- Production-grade secret storage (Vault/KMS)
- Full OAuth provider compliance validation

The goal is architectural clarity and operational correctness, not feature completeness.

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
    keys/ (local-only, not committed)
docs/
Makefile
docker-compose.yml
```

---

## License

For demonstration and portfolio purposes.
