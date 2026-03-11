# Development Guide

Day-to-day commands and workflows for developing Open CIS.

## Running Development Servers

=== "API (Terminal 1)"

    ```bash
    cd api
    source .venv/bin/activate
    uvicorn src.main:app --reload --port 8000
    ```

=== "Frontend (Terminal 2)"

    ```bash
    cd web
    pnpm dev
    ```

## Testing

### Python API Tests

```bash
cd api && pytest
```

### Frontend Tests

```bash
cd web && pnpm test          # Run once
cd web && pnpm test:watch    # Watch mode
```

## Code Quality

### Python

```bash
cd api && ruff check .       # Lint
cd api && mypy src/          # Type check
```

### Frontend

```bash
cd web && pnpm lint          # ESLint
cd web && pnpm typecheck     # TypeScript check
```

## Database Operations

### After Prisma Schema Changes

```bash
cd api
prisma generate
prisma migrate dev
```

### Browse Database

```bash
cd api && prisma studio
```

### Create Migration Without Applying

```bash
cd api && prisma migrate dev --create-only --name migration_name
```

## Docker & Infrastructure

### Check Container Status

```bash
docker compose ps
```

### View Logs

```bash
docker compose logs -f ehrbase
docker compose logs -f ehrbase-db
docker compose logs -f app-db
```

### Rebuild a Service

```bash
docker compose up -d --build ehrbase
```

## EHRBase Operations

### Check Status

```bash
curl http://localhost:8080/ehrbase/rest/status
```

### List Templates

```bash
curl http://localhost:8080/ehrbase/rest/definition/template/adl1.4
```

### Create an EHR Manually

```bash
curl -X POST http://localhost:8080/ehrbase/rest/ehr \
  -H "Content-Type: application/json" \
  -H "Prefer: return=representation"
```

## Coding Standards

| Language | Standard |
|----------|----------|
| Python | Type hints required everywhere (enforced by mypy), all functions async |
| TypeScript | Strict mode enabled, no implicit any |
| HTTP | Use `httpx.AsyncClient` for async requests (never `requests`) |
| Database | Prisma client is async-only (`interface = "asyncio"`) |
