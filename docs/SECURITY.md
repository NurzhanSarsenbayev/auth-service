# Security

This document describes the security model of the Auth Service: trust boundaries, threat model, token/cookie design,
and known limitations.

> Scope note: this is a portfolio-grade prototype. The goal is to be explicit and honest about what is implemented
> and what is intentionally out of scope.

---

## Trust boundaries

### Untrusted inputs
- **External clients** (browsers, mobile apps, scripts) are untrusted.
- **Access / refresh tokens** are untrusted input until verified.
- **OAuth callbacks** are untrusted until verified against the provider.

### Trusted components
- Auth Service is the **token issuer** and must protect the **RSA private key** used for signing.
- PostgreSQL and Redis are trusted infrastructure components in the local deployment model.

### Downstream services
- Downstream services must treat access tokens as untrusted input and verify:
  - signature (JWKS),
  - standard claims (exp/iat/iss/aud as applicable),
  - token type (access),
  - application claims (sub, roles, etc.).

## Trust Model

- X-Forwarded-For headers are trusted only when TRUST_PROXY_HEADERS=true.
- OAuth providers are treated as external identity authorities.
- Redis is considered internal infrastructure.
- PostgreSQL is not exposed to public clients.
- Private keys must never be committed to the repository.

Security boundaries are explicit and documented.

---

## Key handling (RS256 / JWKS)

### Repository policy
- **No private keys are committed to git.**
- Keys must be provided at runtime via mounted volume (see `auth_service/keys/README.md`).

### Runtime expectations
- Service fails fast on startup if key files are missing (misconfiguration should not become a runtime surprise).

### JWKS
- Public key is exposed via JWKS endpoint for downstream verification.
- Key rotation is not implemented yet (see Planned improvements).

---

## Token model

### Access tokens (stateless)
- Signed with RS256.
- Intended to be verified by downstream services using JWKS.
- Short-lived by design (TTL defined in configuration).
- Token type is validated (`type=access`) where applicable.

### Refresh tokens (cookie-based)
- Refresh token is stored in an **HTTP-only cookie**.
- Cookie security settings:
  - `HttpOnly=true`
  - `Secure=true` outside testing mode
  - `SameSite=Strict`
- Refresh flow rotates the refresh token (new refresh is stored in the HTTP-only cookie).
- The API response body returns only a new access token (refresh is never returned in JSON).

### Revocation / logout
- Refresh token revocation is implemented via **Redis blacklist** keyed by `jti` with TTL until token expiration.
- Access tokens are stateless and are not centrally revoked (see Limitations).

---

## CSRF considerations

- The refresh token is stored in an HTTP-only cookie, which could introduce CSRF risk.
- Mitigation in this project:
  - `SameSite=Strict` is used for the refresh cookie, which prevents sending the cookie in cross-site requests
    in typical browser scenarios.
- Not implemented:
  - CSRF double-submit token / per-request CSRF header for refresh endpoint.
  - Origin/Referer enforcement for state-changing endpoints.
- If this service is deployed in a more complex browser scenario (e.g., cross-site frontends, embedded flows),
  additional CSRF defenses must be implemented.

---

## Rate limiting and client identity

- Rate limiting is enforced per subject and path using Redis sliding window.
- Client IP is derived as follows:
  - By default, `request.client.host` is used.
  - `X-Forwarded-For` is used **only** when `TRUST_PROXY_HEADERS=true` (service is behind a trusted reverse proxy).
- This prevents spoofing client identity when the service is exposed directly.

---

## OAuth security notes

- OAuth providers supported: Google, Yandex.
- Authorization code flow is used with server-side callback handling.
- The service trusts provider responses only after validating the received tokens/data from the provider.

Not implemented (out of scope for this prototype):
- Provider token introspection / advanced session management.
- Defense-in-depth controls such as strict allowlists for redirect URIs beyond provider configuration.

---

## Secrets and configuration

- Secrets are provided via local `.env` files for local runs (samples are included, secrets are not committed).
- Recommended production approach (not implemented here):
  - secret manager / vault,
  - short-lived credentials,
  - least-privilege DB users,
  - audit and rotation policies.

---

## What is NOT implemented (known limitations)

- Access token revocation / introspection endpoint (access tokens are stateless).
- Key rotation and multiple active keys (JWKS currently exposes the current public key only).
- Multi-factor authentication (MFA).
- Advanced anomaly detection / account takeover mitigation.
- Full CSRF hardening for refresh endpoint beyond SameSite=Strict.
- Distributed session management beyond refresh token blacklist.
- Formal security audit.

---

## Planned improvements (production hardening roadmap)

- Key rotation strategy:
  - support multiple keys in JWKS,
  - staged rotation (publish new key, sign with new key, keep old key until TTL passes),
  - operational runbook.
- Stronger CSRF defenses for refresh endpoint (token/header or Origin checks).
- Security headers and stricter cookie scoping (domain/path).
- Audit log / security events stream (login attempts, token refresh, role changes).
- Secrets management (vault/secret manager) and environment hardening.

---
