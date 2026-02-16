# Operations

This document describes manual standalone operation of the service.

For a fully reproducible end-to-end validation, use:

```bash
make demo
```

See `docs/DEMO.md` for details.

---

## Standalone Lifecycle

### 0) Ensure RSA keys exist

The service fails fast if RSA key material is missing.

Keys must be available in:

```
auth_service/keys/
```

You can generate keys using the same flow as the demo (`docs/DEMO.md`),
or mount your own key pair (instructions in `auth_service/keys/README.md`).

---

### 1) Configure environment

Create the environment file:

```bash
make init-env
```

This copies:

```
auth_service/.env.auth.sample
```

to:

```
auth_service/.env.auth
```

Review and adjust values if necessary.

#### Running behind a reverse proxy (optional)

By default the service does **not** trust forwarded headers.

- Set `TRUST_PROXY_HEADERS=true` only if the service is behind a trusted reverse proxy.
- If possible, set `TRUSTED_PROXY_IPS` (comma-separated) to allow forwarded headers only from that proxy.
- If you terminate TLS in front of the service, set `COOKIE_SECURE=true` so the refresh cookie is marked as `Secure`.

---

### 2) Start services

```bash
make up
```

Check liveness:

```bash
make health
```

Check readiness:

```bash
make ready
```

* **healthz** -> process is running
* **readyz** -> Postgres and Redis are reachable
* `readyz` returns **503** if dependencies are unavailable

You can also call:

* `/api/v1/healthz`
* `/api/v1/readyz`

directly via curl or browser.

---

### 3) Initialize database (explicit)

The service does not auto-run migrations.

Run:

```bash
make migrate
```

Seed roles:

```bash
make seed-roles
```

No implicit bootstrap logic is executed at startup.

---

### 4) Create superuser (optional)

Superuser creation requires explicit configuration.

If `SUPERUSER_PASSWORD` is set in `.env.auth`, run:

```bash
make create-superuser
```

If not configured, this step is intentionally skipped.

---

## Logs

Inspect container state:

```bash
make ps
```

View logs:

```bash
make logs-auth
make logs-postgres-auth
make logs-redis
```

---

## Troubleshooting

### Service exits immediately (fail-fast)

* Verify RSA keys exist in `auth_service/keys/`
* Verify `auth_service/.env.auth` is present
* Check logs: `make logs-auth`

The service intentionally does not start in degraded mode.

---

### `readyz` returns 503

* Verify Postgres and Redis containers are healthy: `make ps`
* Check logs:

  * `make logs-postgres-auth`
  * `make logs-redis`
  * `make logs-auth`

---

### Health check fails

1. Confirm containers are running: `make ps`
2. Inspect logs: `make logs-auth`
3. Verify environment configuration
4. Restart cleanly:

```bash
make down
make up
make health
make ready
```

---

## Clean shutdown

```bash
make down
```

This stops all containers but preserves volumes unless explicitly removed.

---
## Local quality checks (host tooling)

`make check` runs host tools (ruff, mypy, pre-commit). You must have a local virtualenv with dev dependencies installed.

```bash
python -m venv venv
source venv/Scripts/activate  # Windows Git Bash
pip install -r auth_service/requirements.dev.txt
make check
```

Optional auto-fix:

```bash
make lint-fix
```

---
