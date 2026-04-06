# ADR-0010: OIDC Provider for Open CIS Authentication

**Date:** 2026-04-06

## Status

Accepted

## Context

Open CIS needs an OAuth2/OIDC authorization server to serve two use cases:

1. **CIS user authentication** — Clinicians, nurses, and admins log into the Open CIS frontend using an Authorization Code Flow with PKCE. The backend validates the resulting JWT to identify the user and enforce role-based access control.

2. **SMART App Launch** (PRD-0006, future) — External SMART on FHIR apps launch into Open CIS and request scoped access to FHIR endpoints. The same OIDC provider issues SMART access tokens.

### Options Evaluated

- **Option A — Custom auth in FastAPI**: Rejected. Building auth logic from scratch is high-risk and cannot serve SMART App Launch.
- **Option B — Keycloak**: Rejected for prototype. ~500 MB image with complex configuration. Right choice for production.
- **Option C — Dex (CNCF)**: Small (~20 MB), standards-compliant OIDC provider. Single YAML config file. Can use existing `app-db` Postgres instance.

## Decision

We use **Dex** as the OIDC provider for local development and the prototype stage.

The application is written against the standard OIDC interface — no Dex-specific code:

- Backend reads `OIDC_ISSUER` from environment, fetches OIDC discovery, validates JWTs via JWKS.
- Frontend uses Authorization Code Flow with PKCE, reading endpoints from OIDC discovery.

Swapping to Keycloak requires only changing `OIDC_ISSUER`.

### Role mapping

Roles are managed in the Open CIS `User` table. On first login, the backend upserts a `User` record keyed on the OIDC `sub` claim, defaulting to `CLINICIAN`. Role elevation is done by an admin directly in the database.

## Consequences

**Positive:**
- `docker compose up` produces a fully working auth stack.
- Application code is OIDC-provider-agnostic from day one.
- Dex's static password database gives all contributors identical seeded test users.
- The same infrastructure serves SMART App Launch (PRD-0006).

**Negative:**
- Dex has no admin UI. Managing users beyond static accounts requires editing YAML config.
- Dex's SMART scope support is generic OAuth2. The `/.well-known/smart-configuration` endpoint must be implemented in FastAPI.

**Upgrade path:**
Replace Dex with Keycloak by changing `OIDC_ISSUER` and registering redirect URIs.
