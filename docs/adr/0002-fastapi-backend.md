# ADR 0002: Use FastAPI for Backend

## Status

Accepted

## Context

We need a backend framework to:
- Serve REST API endpoints
- Integrate with EHRBase (HTTP client)
- Integrate with PostgreSQL (Prisma)
- Handle async operations efficiently

Options considered:
1. **FastAPI** (Python) - Modern async Python framework
2. **Express/Fastify** (Node.js) - JavaScript/TypeScript backend
3. **Django** (Python) - Full-featured Python framework
4. **Go** - High-performance compiled language

## Decision

We will use **FastAPI** with **Python 3.11+**.

## Rationale

- **Async-first**: Native async/await support, important for I/O-bound operations (HTTP to EHRBase, database queries)
- **Type hints**: First-class Pydantic integration for request/response validation
- **OpenAPI**: Automatic API documentation generation
- **Learning curve**: Python is accessible, FastAPI is well-documented
- **Ecosystem**: Good libraries for HTTP (httpx), database (Prisma), testing (pytest)

## Consequences

### Positive
- Clean async code with httpx for EHRBase communication
- Automatic request validation and documentation
- Pydantic models shared between API and service layers

### Negative
- Python type system less strict than TypeScript or Go
- Need virtual environment management
- Slightly more complex deployment than Node.js

### Technical Decisions
- Use `httpx` for async HTTP client (EHRBase)
- Use `prisma-client-py` for database access
- Use `pydantic-settings` for configuration
- Use `pytest-asyncio` for testing
