# Operations

> For a reproducible end-to-end run, use `make demo` (see `docs/DEMO.md`).

## Standalone run
### 1) Configure environment
```bash
cp auth_service/.env.auth.sample auth_service/.env.auth
```

### 2) Start services

```bash
make up
make health
make ready
```
---

## Probes (health/readiness)

Health (liveness-style):

```bash
make health
```
Readiness (checks Postgres + Redis):

```bash
make ready
```
Expected behavior:

- 200 OK when **Postgres** and **Redis** are reachable

- 503 **Service Unavailable** when at least one dependency is down

Direct calls:
- curl -s http://localhost:8000/api/v1/healthz
- curl -s -i http://localhost:8000/api/v1/readyz

---

## Database initialization (explicit)

```bash
make migrate
make seed-roles
```

## Superuser creation (optional)

Superuser is created **only** when `SUPERUSER_PASSWORD` is set:

```bash
make create-superuser
```

## Logs and troubleshooting

```bash
make ps
make logs-auth
make logs-postgres-auth
make logs-redis
```

If health check fails:

1. Check container status: `make ps`
2. Check logs: `make logs-auth`
3. Verify env file exists: `auth_service/.env.auth`
4. Recreate from scratch: `make down && make up && make health && make ready`

## Clean shutdown

```bash
make down
```
