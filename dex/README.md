# Dex OIDC Provider

[Dex](https://dexidp.io/) is the OIDC provider for Open CIS authentication. It runs as a Docker Compose service locally and as a standalone Railway service for staging/demo deployments.

## Files

| File | Purpose |
|---|---|
| `config.yaml` | Local development config. Used by `docker-compose.yml`. Concrete values, no env substitution. |
| `config.railway.yaml` | Railway/production config. Uses `${VAR}` placeholders populated from Railway environment variables. |
| `Dockerfile` | Image built for Railway — extends the upstream Dex image and copies `config.railway.yaml` into it. |
| `railway.toml` | Railway service config (Dockerfile path, healthcheck, restart policy). |

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
2. **Settings → Source**: connect the same GitHub repo, branch `main`
3. The `dex/railway.toml` file already configures the Dockerfile path and healthcheck — no extra Railway settings are needed
4. **Settings → Networking → Public Networking**: generate a domain (e.g. `dex-open-cis.up.railway.app`)

### 2. Set environment variables

On the **dex** service, set only two variables:

| Variable | Example value |
|---|---|
| `DEX_ISSUER` | `https://dex-open-cis.up.railway.app/dex` |
| `DEX_REDIRECT_URI` | `https://open-cis-web.up.railway.app/auth/callback` |

`DEX_ISSUER` **must** match the public URL of the Dex service exactly (including `/dex` path).

`DEX_REDIRECT_URI` **must** match the public URL of the `web` service + `/auth/callback`.

> **Note:** `DEX_EXPAND_ENV=true` is already baked into the Dockerfile so Dex can substitute the two placeholders above. Demo password hashes are hardcoded in `config.railway.yaml` (they are not secrets — just one-way hashes of the known demo passwords `admin` and `clinician`).

### 3. (Optional) Change the demo passwords

The default demo accounts are `admin@open-cis.local` (password `admin`) and `clinician@open-cis.local` (password `clinician`). To change them, edit `dex/config.railway.yaml` and replace the bcrypt hashes:

```bash
# Python one-liner (requires bcrypt: pip install bcrypt)
python3 -c "import bcrypt; print(bcrypt.hashpw(b'your-password', bcrypt.gensalt(10)).decode())"

# Or with htpasswd
htpasswd -bnBC 10 "" 'your-password' | tr -d ':\n'
```

Paste the result (starts with `$2b$10$…`, exactly 60 characters) into the `hash:` field in `config.railway.yaml`, commit, and redeploy.

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

## Login Page Customization

The login page branding is controlled by the `frontend:` block in both `config.yaml` and `config.railway.yaml`:

```yaml
frontend:
  issuer: "Open CIS"       # Shown as the provider name
  theme: "light"           # Built-in: "light" or "coreos"
  # logoURL: "<public URL>"  # Optional — replaces the default Dex logo
```

For a full HTML/CSS rebrand, copy Dex's upstream [`web/`](https://github.com/dexidp/dex/tree/v2.39.1/web) directory into this repo (e.g. `dex/web/`), customize `templates/` and `static/`, bake it into `dex/Dockerfile` (`COPY dex/web /srv/dex/web`), and set `frontend.dir: /srv/dex/web` in `config.railway.yaml`.

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
