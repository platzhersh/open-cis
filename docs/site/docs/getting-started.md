# Getting Started

This guide walks you through setting up Open CIS for local development.

## Prerequisites

- **Docker** and **Docker Compose** (for EHRBase and PostgreSQL)
- **Python 3.11+** (for the API)
- **pnpm** (for the frontend)

!!! tip "Python version"
    If you don't have Python 3.11+, install it via [pyenv](https://github.com/pyenv/pyenv):
    ```bash
    brew install pyenv
    pyenv install 3.11
    pyenv local 3.11
    ```

## Automated Setup

The fastest way to get started:

```bash
git clone https://github.com/platzhersh/open-cis.git
cd open-cis
./scripts/setup.sh
```

## Manual Setup

### 1. Start Infrastructure

```bash
docker compose up -d
```

This starts three containers:

- **ehrbase** -- openEHR Clinical Data Repository (port 8080)
- **ehrbase-db** -- PostgreSQL for EHRBase (port 5433)
- **app-db** -- PostgreSQL for application data (port 5454)

!!! warning "EHRBase startup delay"
    EHRBase takes 30-60 seconds to become available. Wait for the health check to pass before starting the API:
    ```bash
    curl http://localhost:8080/ehrbase/rest/status
    # Expected: {"status":"UP"}
    ```

### 2. Set Up the Python API

```bash
cd api
python3.11 -m venv .venv
source .venv/bin/activate    # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
prisma generate
prisma migrate dev --name init
```

### 3. Set Up the Frontend

```bash
cd web
pnpm install
```

### 4. Run Development Servers

Open two terminals:

=== "Terminal 1 -- API"

    ```bash
    cd api
    source .venv/bin/activate
    uvicorn src.main:app --reload --port 8000
    ```

=== "Terminal 2 -- Frontend"

    ```bash
    cd web
    pnpm dev
    ```

## Health Check

Verify all services are running:

```bash
# Docker containers
docker compose ps
# Expected: app-db, ehrbase-db, ehrbase all "Up" and healthy

# EHRBase
curl http://localhost:8080/ehrbase/rest/status
# Expected: {"status":"UP"}

# Backend API
curl http://localhost:8000/api/patients
# Expected: [] (empty array if no patients)

# Frontend
open http://localhost:5173
# Expected: Patients page loads without CORS errors
```

## Service URLs

| Service | URL |
|---------|-----|
| Frontend | [http://localhost:5173](http://localhost:5173) |
| Backend API | [http://localhost:8000](http://localhost:8000) |
| API Docs (Swagger) | [http://localhost:8000/docs](http://localhost:8000/docs) |
| API Docs (ReDoc) | [http://localhost:8000/redoc](http://localhost:8000/redoc) |
| OpenAPI Schema | [http://localhost:8000/openapi.json](http://localhost:8000/openapi.json) |
| EHRBase | [http://localhost:8080/ehrbase/rest](http://localhost:8080/ehrbase/rest) |
| App Database | localhost:5454 (PostgreSQL) |
| EHRBase Database | localhost:5433 (PostgreSQL) |

## Environment Variables

Copy `.env.example` to `.env` and configure:

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | Prisma connection to app database | `postgresql://...` |
| `EHRBASE_URL` | EHRBase REST API endpoint | `http://localhost:8080/ehrbase/rest` |
| `CORS_ORIGINS` | JSON array of allowed origins | `["http://localhost:5173"]` |
| `VITE_API_URL` | Frontend API base URL | `http://localhost:8000` |

## Seed Data

For local development with sample data:

```bash
# Basic patient demographics
python scripts/seed.py

# Full staging data with synthetic vitals
python scripts/seed_staging.py
```

See [ADR-0005: Synthetic Data Generation](decisions/0005-synthetic-data.md) for details on the seeding approach.
