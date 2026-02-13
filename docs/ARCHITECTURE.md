# Architecture

## Overview
This repository provides a standalone **Auth Service** for issuing and validating JWT tokens using **RS256** and a **JWKS**
endpoint. The service persists data in **PostgreSQL**. **Redis** required for standalone demo.

## Components
- **Auth API (FastAPI)**: HTTP API for authentication flows, token issuance, and authorization checks.
- **PostgreSQL**: persistent storage (users, roles, refresh tokens, and other auth-related state).
- **Redis (optional)**: auxiliary storage for caching and/or rate limiting (configuration-dependent).

## High-level request flow
1. Client calls an auth endpoint (e.g., login/refresh).
2. Auth Service validates credentials / refresh token and checks account state.
3. Service issues JWT tokens signed with **private RSA key**.
4. Public keys are exposed via **JWKS** for downstream services to verify access tokens.

## Key material
- Private key is **not stored in the repository**.
- Keys are generated locally and mounted/provided via environment/volume.
- See `docs/SECURITY.md` for details.

## Operational principles
- **No magic on boot**: container startup only starts the API process.
- Migrations and initialization are executed explicitly via `make` commands.
- A single canonical standalone Compose path is used for local run.
