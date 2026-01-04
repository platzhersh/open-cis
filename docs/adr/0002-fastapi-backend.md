# 2. Use FastAPI for Backend

Date: 2026-01-02

## Status

Accepted

## Context

We need a backend framework to serve REST API endpoints, integrate with EHRBase via HTTP, integrate with PostgreSQL through Prisma, and handle async operations efficiently.

Four approaches were considered. FastAPI is a modern Python framework with first-class async/await support and automatic OpenAPI documentation. Express or Fastify on Node.js would provide JavaScript/TypeScript consistency with the frontend and excellent async patterns. Django offers a full-featured Python framework with an extensive ecosystem and built-in admin interface. Go would provide high performance and strong typing through a compiled language.

The backend will primarily perform I/O-bound operations: making HTTP requests to EHRBase, executing database queries, and serving JSON responses. These operations benefit more from efficient async handling than raw CPU performance. The team values type safety for catching errors early, automatic API documentation for development velocity, and a gentle learning curve that allows focus on openEHR concepts rather than framework complexity.

## Decision

We will use FastAPI with Python 3.11 or later as the backend framework.

We will use httpx as the async HTTP client for communicating with EHRBase, prisma-client-py for database access, pydantic-settings for configuration management, and pytest-asyncio for testing. All application code will use Python's native async/await syntax, and we will leverage Pydantic models throughout the service and API layers for consistent type validation.

## Consequences

FastAPI's async-first architecture allows us to write clean, readable code for concurrent I/O operations without blocking threads or managing callback chains. The automatic request validation and OpenAPI documentation generation means we spend less time writing boilerplate validation code and manually maintaining API specifications. Pydantic models can be shared between API endpoints and service layers, ensuring type consistency throughout the application.

However, Python's type system is less strict than TypeScript or Go, relying on optional static analysis with mypy rather than compile-time guarantees. We will need to manage Python virtual environments for dependency isolation, adding a step to the development setup compared to Node.js or Go. Deployment is slightly more complex than Node.js containerized applications, as we must ensure the correct Python runtime and activate virtual environments appropriately.

The learning curve for FastAPI and async Python is accessible enough that developers can become productive quickly, allowing the team to focus energy on understanding openEHR rather than fighting the framework.
