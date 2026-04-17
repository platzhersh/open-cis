# Dex OIDC Provider

[Dex](https://dexidp.io/) is the OIDC provider for Open CIS authentication. It runs as a Docker Compose service locally and as a standalone Railway service for staging/demo deployments.

## Files

| File | Purpose |
|---|---|
| `config.yaml` | Local development config. Used by `docker-compose.yml`. Concrete values, no env substitution. |
| `config.railway.yaml` | Railway/production config. Uses `${VAR}` placeholders populated from Railway environment variables. |

## Local Development

No extra steps — `docker compose up` mounts `config.yaml` into the Dex container.

The default seeded users are:

| Email | Password | Role (default) |
|---|---|---|
| `admin@open-cis.local` | `admin` | `CLINICIAN` (promote to `ADMIN` in DB) |
| `clinician@open-cis.local` | `clinician` | `CLINICIAN` |

Role elevation is done in the app database, not in Dex. See `api/prisma/schema.prisma`.

## Railway Deployment

Dex runs on Railway as a separate service alongside `api`, `web`, and `app-db`. This section covers adding and configuring that service.

### 1. Create the Dex service

In the Railway project:

1. **New → Empty Service** (name it `dex`)
2. **Settings → Source**: connect the same GitHub repo
3. **Settings → Build**: select *Dockerfile* and set:
   ```
   Root Directory: dex
   Dockerfile Path: Dockerfile
   ```
4. Create a minimal `dex/Dockerfile` in the repo (if not already present):
   ```Dockerfile
   FROM ghcr.io/dex-idp/dex:v2.39.1
   COPY config.railway.yaml /etc/dex/config.yaml
   EXPOSE 5556
   CMD ["dex", "serve", "/etc/dex/config.yaml"]
   ```
5. **Settings → Networking → Public Networking**: generate a domain (e.g. `dex-open-cis.up.railway.app`)

### 2. Set environment variables

On the **dex** service, set:

| Variable | Example value |
|---|---|
| `DEX_ISSUER` | `https://dex-open-cis.up.railway.app/dex` |
| `DEX_REDIRECT_URI` | `https://open-cis-web.up.railway.app/auth/callback` |
| `DEX_DEMO_ADMIN_HASH` | *(see below)* |
| `DEX_DEMO_CLINICIAN_HASH` | *(see below)* |

`DEX_ISSUER` **must** match the public URL of the Dex service exactly (including `/dex` path).

`DEX_REDIRECT_URI` **must** match the public URL of the `web` service + `/auth/callback`.

### 3. Generate bcrypt password hashes

The demo passwords are hashed with bcrypt (cost 10). The default hashes in `.env.example` correspond to the passwords `admin` and `clinician`. **Replace them for any deployment you share a public URL for.**

To generate new hashes:

```bash
# Python one-liner (requires bcrypt: pip install bcrypt)
python3 -c "import bcrypt; print(bcrypt.hashpw(b'your-password', bcrypt.gensalt(10)).decode())"

# Or with htpasswd
htpasswd -bnBC 10 "" 'your-password' | tr -d ':\n'
```

Copy each hash directly into the Railway env var panel. Hashes start with `$2b$10$…`. Escape any `$` signs if your deployment tool requires it (Railway's UI does not).

### 4. Configure the `api` service

On the **api** service, set:

| Variable | Value |
|---|---|
| `OIDC_ISSUER` | Same as `DEX_ISSUER` above |
| `OIDC_CLIENT_ID` | `open-cis-web` |

### 5. Configure the `web` service

On the **web** service, set:

| Variable | Value |
|---|---|
| `VITE_OIDC_ISSUER` | Same as `DEX_ISSUER` above |
| `VITE_OIDC_CLIENT_ID` | `open-cis-web` |
| `VITE_APP_MODE` | `demo` *(optional — shows credential hints on login page)* |

### 6. Verify

After all services deploy, check:

```bash
curl https://dex-open-cis.up.railway.app/dex/.well-known/openid-configuration
```

You should see a valid OIDC discovery document with `authorization_endpoint`, `token_endpoint`, and `jwks_uri` all pointing at the Dex public URL.

Then log into the web app — the Dex login page should appear, accept the demo credentials, and redirect back to the frontend authenticated.

## Storage: Memory vs Postgres

The Railway config uses `storage: type: memory`. This is intentional for demo deployments:

- All sessions are lost on Dex restart (users re-authenticate)
- No dynamic client registration is persisted
- Zero extra infrastructure required

For longer-lived staging or production, switch `config.railway.yaml` to Postgres storage and point at a Railway Postgres plugin:

```yaml
storage:
  type: postgres
  config:
    host: ${DEX_DB_HOST}
    port: 5432
    database: ${DEX_DB_NAME}
    user: ${DEX_DB_USER}
    password: ${DEX_DB_PASSWORD}
    ssl:
      mode: require
```

## Notes on the Client Configuration

The `open-cis-web` client is configured as a **public client** (`public: true`, no `secret`). This is correct for SPA clients that cannot safely hold a secret — security relies on PKCE + the registered redirect URI.

Do not add a `secret:` field unless you also move the token exchange out of the browser and into the FastAPI backend.

## Upgrading to Keycloak

This prototype uses Dex. To swap to Keycloak (or any other OIDC provider) in production:

1. Register a public client named `open-cis-web` with the same redirect URI
2. Update `OIDC_ISSUER` / `VITE_OIDC_ISSUER` to the new realm URL
3. No application code changes are required — validation goes through the OIDC discovery document

See [ADR-0010](../docs/adr/0010-oidc-provider-choice.md) for the full rationale.
