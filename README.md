# Open CIS

A minimal Clinical Information System built on openEHR/EHRBase for learning and experimentation.

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
cd api && source .venv/bin/activate && uvicorn src.main:app --reload --port 8000

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
- **API Docs**: http://localhost:8000/docs
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

## Architecture

See [CONTEXT.md](./CONTEXT.md) for detailed architecture and AI context.
