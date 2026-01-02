# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Open CIS is a minimal Clinical Information System built on openEHR/EHRBase for learning and experimentation. See [CONTEXT.md](./CONTEXT.md) for detailed architecture, tech stack, and domain concepts.

## Development Commands

### Initial Setup
```bash
# Run automated setup script (recommended)
./scripts/setup.sh

# Or manually:
docker compose up -d                    # Start infrastructure

# Python 3.11+ required - install via pyenv if needed:
# brew install pyenv
# pyenv install 3.11
# pyenv local 3.11

cd api && python3.11 -m venv .venv      # Or 'python -m venv .venv' if python3.11 is default
source .venv/bin/activate               # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
prisma generate
prisma migrate dev --name init
cd ../web && pnpm install
```

### Running Development Servers
```bash
# Terminal 1 - API (must activate venv first)
cd api && source .venv/bin/activate && uvicorn src.main:app --reload --port 8000

# Terminal 2 - Frontend
cd web && pnpm dev
```

### Testing
```bash
# Python API tests
cd api && pytest

# Frontend tests
cd web && pnpm test              # Run once
cd web && pnpm test:watch        # Watch mode
```

### Code Quality
```bash
# Python linting and type checking
cd api && ruff check .           # Lint
cd api && mypy src/              # Type check

# Frontend linting and type checking
cd web && pnpm lint              # ESLint
cd web && pnpm typecheck         # TypeScript check
```

### Database Operations
```bash
# After Prisma schema changes
cd api && prisma generate && prisma migrate dev

# Browse database
cd api && prisma studio

# Create migration without applying
cd api && prisma migrate dev --create-only --name migration_name
```

### Docker & Infrastructure
```bash
# Check EHRBase status (wait 30-60s after docker compose up)
curl http://localhost:8080/ehrbase/rest/status

# View logs
docker compose logs -f ehrbase
docker compose logs -f ehrbase-db
docker compose logs -f app-db

# Rebuild specific service
docker compose up -d --build ehrbase
```

### EHRBase Operations
```bash
# List templates
curl http://localhost:8080/ehrbase/rest/definition/template/adl1.4

# Create EHR manually
curl -X POST http://localhost:8080/ehrbase/rest/ehr \
  -H "Content-Type: application/json" \
  -H "Prefer: return=representation"
```

## Code Organization

### Service Layer Pattern (Python API)
Each domain module (e.g., `api/src/patients/`) follows this structure:
- `router.py`: FastAPI route definitions and HTTP handling
- `service.py`: Business logic layer (orchestrates repository and EHRBase calls)
- `repository.py`: Prisma database operations (when app DB is used)
- `schemas.py`: Pydantic models for request/response validation

### EHRBase Integration (`api/src/ehrbase/`)
- `client.py`: Core EHRBase REST API client (singleton: `ehrbase_client`)
- `compositions.py`: Helpers for creating/parsing compositions
- `templates.py`: Template management utilities
- `queries.py`: AQL query builders and executors

### Frontend Structure (`web/src/`)
- `pages/`: Vue components for routes
- `stores/`: Pinia state management
- `composables/`: Reusable composition functions
- `types/`: TypeScript type definitions
- `lib/`: UI component library (shadcn-vue)

## Important Notes

### EHRBase Startup Delay
EHRBase takes 30-60 seconds to become available after `docker compose up`. Always check `/ehrbase/rest/status` before running the API.

### Port Configuration
- Frontend dev server: `http://localhost:5173`
- Backend API: `http://localhost:8000`
- EHRBase REST API: `http://localhost:8080/ehrbase/rest`
- App PostgreSQL: `localhost:5454`
- EHRBase PostgreSQL: `localhost:5433`

### Environment Variables
Copy `.env.example` to `.env` (locally) and configure:
- `DATABASE_URL`: Prisma connection to app database
- `EHRBASE_URL`: EHRBase REST API endpoint
- `CORS_ORIGINS`: JSON array of allowed origins
- `VITE_API_URL`: Frontend API base URL

### Coding Standards
- **Python**: Type hints required everywhere (enforced by mypy config), all functions must be `async`
- **TypeScript**: Strict mode enabled, no implicit any
- **HTTP**: Use `httpx.AsyncClient` for async requests (never `requests`)
- **Database**: Prisma client is async-only (`interface = "asyncio"`)

### Railway Deployment
Each service has a `railway.toml` for deployment configuration. See individual service directories for details.
