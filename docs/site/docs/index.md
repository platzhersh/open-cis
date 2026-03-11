# Open CIS

**A minimal Clinical Information System built on openEHR/EHRBase for learning and experimentation.**

---

Open CIS is an open-source project that demonstrates how to build a modern clinical application on top of the [openEHR](https://www.openehr.org/) standard. It pairs a Vue 3 frontend with a FastAPI backend that stores clinical data in [EHRBase](https://ehrbase.org/), an open-source openEHR Clinical Data Repository.

The project was built in public as a learning exercise, documented through a [six-part blog series](blog-series/index.md) on Medium, and ultimately led to the creation of [oehrpy](oehrpy/index.md), a standalone Python SDK for openEHR.

## Key Features

- **Dual-database architecture** -- clinical data in EHRBase (openEHR), app data in PostgreSQL via Prisma
- **Vital signs recording** with blood pressure and pulse, stored as openEHR compositions
- **Patient management** with MRN-to-EHR linking
- **openEHR transparency** -- inspect the underlying archetype data from the UI
- **One-click deployment** on Railway

## Tech Stack

| Layer | Technology |
|-------|------------|
| Frontend | Vue 3 + TypeScript + Vite + shadcn-vue + Tailwind + Pinia |
| Backend | FastAPI + Python 3.11+ + Pydantic |
| Clinical Data | EHRBase (openEHR repository) |
| App Database | PostgreSQL via Prisma (prisma-client-py) |
| Infrastructure | Docker Compose |
| Deployment | Railway |

## Quick Links

- [Getting Started](getting-started.md) -- set up your local dev environment
- [Architecture Overview](architecture/overview.md) -- how the system fits together
- [Blog Series](blog-series/index.md) -- the full build narrative on Medium
- [oehrpy](oehrpy/index.md) -- the Python openEHR SDK born from this project
- [Decisions](decisions/index.md) -- architecture decision records

## Live Demo

**Staging environment**: [open-cis-web-staging.up.railway.app](https://open-cis-web-staging.up.railway.app/)

## Deploy Your Own

[![Deploy on Railway](https://railway.com/button.svg)](https://railway.com/deploy/X4FuWB?referralCode=eFNpqC&utm_medium=integration&utm_source=template&utm_campaign=generic)

Deploy your own instance with one click using the Railway template. Railway provisions the full stack including PostgreSQL databases and automatic deployments from Git.

## Source Code

- [Open CIS on GitHub](https://github.com/platzhersh/open-cis)
- [oehrpy on GitHub](https://github.com/platzhersh/oehrpy)
