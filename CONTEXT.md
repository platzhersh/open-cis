# CIS Experiment - AI Context

## Project Overview
Minimal Clinical Information System built on openEHR/EHRBase.
Personal learning project exploring modern clinical data architecture.

## Tech Stack
- **Frontend**: Vue 3 + TypeScript + Vite + shadcn-vue + Tailwind + Pinia
- **Backend**: FastAPI + Python 3.11+ + Pydantic
- **Clinical Data**: EHRBase (openEHR repository)
- **Terminology**: Snowstorm Lite (FHIR terminology server for SNOMED CT)
- **App Database**: PostgreSQL via Prisma (prisma-client-py)
- **Deployment**: Railway

## Architecture

### Data Split
- **EHRBase**: All clinical data (observations, diagnoses, medications, encounters)
- **PostgreSQL/Prisma**: App data only (users, audit logs, patient registry linking MRN to EHR ID)

### Key Patterns
- Each patient has one EHR in EHRBase
- PatientRegistry in Prisma links MRN → ehrId
- Clinical writes create compositions in EHRBase
- AQL queries for clinical data retrieval
- FastAPI async throughout

## Domain Concepts
- **EHR**: Electronic Health Record - one per patient in EHRBase
- **Composition**: A clinical document (consultation, vital signs, prescription)
- **Archetype**: Reusable clinical model (blood_pressure, medication_order)
- **Template**: Archetypes combined for a use case
- **AQL**: Archetype Query Language for querying clinical data

## File Conventions
- Python: Routers in `router.py`, business logic in `service.py`, Pydantic models in `schemas.py`
- Vue: Pages in `pages/`, composables in `composables/`, Pinia stores in `stores/`
- All Python functions async, use `httpx` for HTTP
- Type hints everywhere (Python + TypeScript)

## API Endpoints
- `GET /health` - Health check
- `POST /api/patients` - Create patient (creates EHR in EHRBase)
- `GET /api/patients` - List patients
- `GET /api/patients/{id}` - Get patient by ID
- `GET /api/patients/mrn/{mrn}` - Get patient by MRN
- `PATCH /api/patients/{id}` - Update patient
- `GET /api/terminology/lookup` - Look up a terminology code
- `GET /api/terminology/validate` - Validate a code
- `GET /api/terminology/expand` - Expand a value set
- `GET /api/terminology/search` - Search for codes by term
- `GET /api/terminology/subsumes` - Test subsumption relationship
- `GET /api/terminology/health` - Terminology server health check
