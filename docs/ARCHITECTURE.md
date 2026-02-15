# Architecture

## Overview
This repository provides a standalone **Auth Service** for issuing and validating JWT tokens using **RS256** and a **JWKS**
endpoint. The service persists data in **PostgreSQL**. **Redis** is required at runtime (rate limiting + token revocation).

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

+-------------------+               +-------------------+
|    PostgreSQL     |               |      Redis        |
|-------------------|               |-------------------|
| Users             |               | Rate limiting     |
| Roles             |               | Token blacklist   |
| Login history     |               +-------------------+
+-------------------+
```

- JWT signing keys are mounted via volume.
- Public keys are exposed via JWKS endpoint.

### Trust Boundaries

- JWT private key is never committed.
- Refresh tokens are revocable via Redis blacklist.
- Proxy headers must only be trusted behind a secure reverse proxy.
- See `docs/SECURITY.md` for threat model and limitations.


## Components
- **Auth API (FastAPI)**: HTTP API for authentication flows, token issuance, and authorization checks.
- **PostgreSQL**: persistent storage (users, roles, refresh tokens, and other auth-related state).
- **Redis (runtime dependency)**: used by the rate limiter and token blacklist (refresh revocation).

## High-level request flow
1. Client calls an auth endpoint (e.g., login/refresh).
2. Auth Service validates credentials / refresh token and checks account state.
3. Service issues JWT tokens signed with **private RSA key**.
4. Public keys are exposed via **JWKS** for downstream services to verify access tokens.

## Key material
- Private key is **not stored in the repository**.
- Keys are generated locally and mounted/provided via environment/volume.
- See `docs/SECURITY.md` for details.

## Operational Principles

The architecture intentionally prioritizes operational clarity over feature density.

- **Explicit runtime dependencies**: PostgreSQL and Redis are required. The service does not run in degraded mode.
- **Fail-fast startup**: the application exits if key material or critical configuration is missing.
- **No implicit bootstrap logic**: migrations, role seeding, and superuser creation are explicit `make` targets.
- **Clear liveness vs readiness separation**: health checks reflect real infrastructure availability.
- **Revocable authentication model**: refresh tokens are stored and can be invalidated.
- **Docker-first reproducibility**: local and CI environments follow the same infrastructure model.
- **Predictable operational surface**: no hidden background workers or side effects on startup.
