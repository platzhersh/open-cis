# Deployment Guide

Open CIS is deployed on [Railway](https://railway.app/) with separate services for the API, frontend, and databases.

## One-Click Deploy

The fastest way to deploy your own instance:

[![Deploy on Railway](https://railway.com/button.svg)](https://railway.com/deploy/X4FuWB?referralCode=eFNpqC&utm_medium=integration&utm_source=template&utm_campaign=generic)

This provisions the full stack: API, frontend, two PostgreSQL databases, and EHRBase.

## Live Environments

| Environment | URL |
|-------------|-----|
| Staging (Web) | [open-cis-web-staging.up.railway.app](https://open-cis-web-staging.up.railway.app/) |

## Railway Configuration

Each service has a `railway.toml` for deployment configuration. The API Dockerfile handles migrations and optional staging data seeding:

```dockerfile
CMD sh -c "prisma migrate deploy && \
  if [ \"$RAILWAY_ENVIRONMENT\" = \"staging\" ]; then \
    python scripts/seed_staging.py; \
  fi && \
  uvicorn src.main:app --host 0.0.0.0 --port ${PORT:-8000}"
```

### Environment Variables

Set these in your Railway project:

| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | Prisma connection string (auto-set by Railway PostgreSQL) |
| `EHRBASE_URL` | EHRBase REST endpoint |
| `CORS_ORIGINS` | JSON array of allowed frontend origins |
| `RAILWAY_ENVIRONMENT` | Set to `staging` for automatic synthetic data seeding |

## Staging Data

When `RAILWAY_ENVIRONMENT=staging` is set, the API automatically seeds synthetic data on startup:

- 15 synthetic patients with realistic demographics
- 2-5 vital signs readings per patient
- Clinically plausible values
- MRN prefix: `STAGING-`
- Idempotent: safe to run on every deployment

See [ADR-0005: Synthetic Data](../decisions/0005-synthetic-data.md) for details.
