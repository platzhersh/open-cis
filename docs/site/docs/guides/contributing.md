# Contributing

Open CIS is an open-source learning project. Contributions are welcome.

## Getting Started

1. Fork the repository on GitHub
2. Clone your fork locally
3. Follow the [Getting Started](../getting-started.md) guide to set up your environment
4. Create a feature branch from `main`

## Development Workflow

1. Make your changes
2. Run tests and linting:

    ```bash
    # API
    cd api && pytest && ruff check . && mypy src/

    # Frontend
    cd web && pnpm test && pnpm lint && pnpm typecheck
    ```

3. Commit with a clear message
4. Push to your fork and open a pull request

## Code Standards

- **Python**: Type hints everywhere, all functions async, `httpx` for HTTP (never `requests`)
- **TypeScript**: Strict mode, no implicit any
- **Database**: Prisma async-only

## Project Structure

```
open-cis/
├── api/                    # FastAPI backend
│   ├── src/
│   │   ├── ehrbase/        # EHRBase integration
│   │   ├── patients/       # Patient module (router, service, repository, schemas)
│   │   └── main.py         # App entrypoint
│   ├── templates/          # OPT template files
│   └── tests/
├── web/                    # Vue 3 frontend
│   └── src/
│       ├── pages/          # Route components
│       ├── stores/         # Pinia state
│       ├── composables/    # Composition functions
│       └── types/          # TypeScript types
├── docs/                   # Documentation
│   ├── adr/                # Architecture Decision Records
│   ├── prd/                # Product Requirements Documents
│   ├── brand/              # Brand kit
│   └── site/               # This documentation site (MkDocs)
└── docker-compose.yml      # Local infrastructure
```

## Areas for Contribution

- **oehrpy SDK**: Help close the [coverage gaps](../oehrpy/coverage.md) (composition update, versioning, new builders)
- **Clinical templates**: Add new openEHR templates and corresponding UI
- **Documentation**: Improve guides, add examples, fix typos
- **Testing**: Increase test coverage for API and frontend

## Related Repositories

- [Open CIS](https://github.com/platzhersh/open-cis) -- this project
- [oehrpy](https://github.com/platzhersh/oehrpy) -- Python openEHR SDK
