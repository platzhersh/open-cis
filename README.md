# Open CIS

A minimal Clinical Information System built on openEHR/EHRBase for learning and experimentation.

## Live Demo

- **Staging Environment**: https://open-cis-web-staging.up.railway.app/

## Deploy Your Own

[![Deploy on Railway](https://railway.com/button.svg)](https://railway.com/deploy/X4FuWB?referralCode=eFNpqC&utm_medium=integration&utm_source=template&utm_campaign=generic)

Deploy your own instance with one click using the Railway template above. Railway makes it easy to deploy the full stack with PostgreSQL databases and automatic deployments from Git.

## Tech Stack

| Layer | Technology |
|-------|------------|
| Frontend | Vue 3 + TypeScript + Vite + shadcn-vue + Tailwind + Pinia |
| Backend | FastAPI + Python 3.11+ + Pydantic |
| Clinical Data | EHRBase (openEHR repository) |
| App Database | PostgreSQL via Prisma (prisma-client-py) |
| Infrastructure | Docker Compose |
| Deployment | Railway |

## Quick Start

```bash
# 1. Start infrastructure
docker compose up -d

# 2. Wait for EHRBase to be ready (can take 30-60 seconds)
curl http://localhost:8080/ehrbase/rest/status

# 3. Setup Python API (requires Python 3.11+)
# If you don't have Python 3.11+, install via pyenv:
#   brew install pyenv
#   pyenv install 3.11
#   pyenv local 3.11

cd api
python3.11 -m venv .venv  # Or 'python -m venv .venv' if python3.11 is default
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
prisma generate
prisma migrate dev --name init

# 4. Setup Vue frontend
cd ../web
pnpm install
pnpm dlx shadcn-vue@latest init

# 5. Run development
# Terminal 1 (API):
cd api && source .venv/bin/activate && prisma migrate deploy && uvicorn src.main:app --reload --port 8000

# Terminal 2 (Web):
cd web && pnpm dev
```

## Health Check

Verify all services are running:

```bash
# Check Docker containers
docker compose ps
# Expected: app-db, ehrbase-db, ehrbase all "Up" and healthy

# Check EHRBase (wait 30-60s after docker compose up)
curl http://localhost:8080/ehrbase/rest/status
# Expected: {"status":"UP"}

# Check backend API
curl http://localhost:8000/api/patients
# Expected: [] (empty array if no patients)

# Check frontend
open http://localhost:5173
# Expected: Patients page loads without CORS errors
```

### Service URLs

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Docs (Swagger)**: http://localhost:8000/docs
- **API Docs (ReDoc)**: http://localhost:8000/redoc
- **OpenAPI Schema**: http://localhost:8000/openapi.json
- **EHRBase**: http://localhost:8080/ehrbase/rest
- **App Database**: localhost:5454 (PostgreSQL)
- **EHRBase Database**: localhost:5433 (PostgreSQL)

## Useful Commands

```bash
# Check EHRBase status
curl http://localhost:8080/ehrbase/rest/status

# Create an EHR manually
curl -X POST http://localhost:8080/ehrbase/rest/ehr \
  -H "Content-Type: application/json" \
  -H "Prefer: return=representation"

# List templates
curl http://localhost:8080/ehrbase/rest/definition/template/adl1.4

# Run API tests
cd api && pytest

# Prisma studio (DB browser)
cd api && prisma studio

# Generate Prisma client after schema changes
cd api && prisma generate && prisma migrate dev
```

## Blog Series

This project is accompanied by a Medium article series documenting the journey of building a clinical information system on openEHR:

1. **[Introduction](https://medium.com/@platzh1rsch/building-open-cis-a-minimal-clinical-information-system-on-openehr-7d3c5d75bae8)** — What is openEHR and why build on it?
2. **[The Modeling Stack](https://medium.com/@platzh1rsch/building-open-cis-part-2-the-clinical-modeling-stack-221c019e65ca?sk=1d3216e585487a0ae623645edec7bbc6)** — Archetypes, templates, and compositions
3. **[FLAT Format Deep Dive](https://medium.com/@platzh1rsch/building-open-cis-part-2b-template-formats-and-the-flat-format-deep-dive-0ed3ff0acfed?sk=fd29cdd22e79dee8818b84fc94ea7429)** — The serialization format that powers EHRBase
4. **[Architecture](https://medium.com/@platzh1rsch/building-open-cis-part-3-going-sdk-less-our-architecture-decisions-134786e090b5?sk=93d3a0d2069bf5923d1f90ba1a1966d3)** — Separating clinical data from application data
5. **[SDK Landscape](https://medium.com/@platzh1rsch/building-open-cis-part-4-the-openehr-sdk-landscape-1b93411ec279?sk=b31af9ea583b7bc5b4bb52f67a9857ba)** — What exists, what's missing
6. **oehrpy** — Building the Python SDK (coming soon)

## Architecture

See [CONTEXT.md](./CONTEXT.md) for detailed architecture and AI context.
