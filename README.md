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

# 3. Setup Python API
cd api
python -m venv .venv
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
