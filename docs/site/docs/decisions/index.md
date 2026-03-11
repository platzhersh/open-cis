# Architecture Decision Records

Architecture Decision Records (ADRs) capture the key technical decisions made during the development of Open CIS, along with their context and consequences.

## Index

| ADR | Title | Date | Status |
|-----|-------|------|--------|
| [ADR-0001](0001-use-openehr.md) | Use openEHR for Clinical Data | 2026-01-02 | Accepted |
| [ADR-0002](0002-fastapi-backend.md) | Use FastAPI for Backend | 2026-01-02 | Accepted |
| [ADR-0003](0003-template-management.md) | openEHR Template Management | 2026-01-03 | Accepted |
| [ADR-0004](0004-direct-httpx-integration.md) | Direct httpx Integration for openEHR API | 2026-01-04 | Accepted |
| [ADR-0005](0005-synthetic-data.md) | Synthetic Data Generation for Staging | 2026-01-05 | Accepted |

## What is an ADR?

An ADR is a short document that captures a significant architectural decision along with its context and consequences. We use the format established by [Michael Nygard](https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions):

- **Context**: What is the situation that requires a decision?
- **Decision**: What did we decide and why?
- **Consequences**: What are the positive and negative implications?

ADRs are immutable once accepted -- if a decision changes, a new ADR is created that supersedes the old one.
