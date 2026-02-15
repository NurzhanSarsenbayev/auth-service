# Capabilities

This document outlines the core capabilities of the service.

These capabilities are intentionally selected to demonstrate operational control over authentication flows,
explicit dependency management, and predictable runtime behavior.
The focus is not feature completeness, but architectural discipline.

---

## Core Capabilities

### Authentication Model

The authentication flow prioritizes explicit token lifecycle control and revocation semantics.

- Access & Refresh tokens (RS256)
- Secure HTTP-only refresh cookie
- Token blacklist (Redis)
- Logout (single token / all tokens)

---

### Authorization Model

Authorization is enforced server-side via role-based access control (RBAC).

- RBAC with role assignment
- Protected endpoints with role enforcement

---

### OAuth Integration

OAuth providers are treated as external identity authorities and require explicit configuration.

- Google OAuth
- Yandex OAuth
- Deterministic fallback username generation

> OAuth providers require environment configuration.

---

### Observability

Operational transparency is provided through structured logging, optional tracing, and explicit health probes.

- Structured logging (LOG_FORMAT=text|json)
- OpenTelemetry tracing (optional via environment)
- Endpoints:
  - GET /api/v1/healthz (liveness)
  - GET /api/v1/readyz (readiness: DB + Redis)
