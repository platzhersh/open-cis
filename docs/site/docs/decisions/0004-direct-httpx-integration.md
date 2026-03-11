# ADR-0004: Direct httpx Integration for openEHR API

**Date:** 2026-01-04 | **Status:** Accepted

## Context

Open CIS needs to interact with EHRBase to create, retrieve, and query clinical compositions. We must decide how to implement this integration: use an existing SDK or build a custom client using a low-level HTTP library.

### Available SDK Options

**EHRbase openEHR SDK (Java)**: Active, feature-rich with ~20 modules, but Java-only and incompatible with our Python backend.

**pyEHR (Python)**: Dormant since ~2018, Python 2 syntax, outdated dependencies (Elasticsearch 1.5), designed for secondary analysis rather than primary EHR operations.

**Other Python options**: None found. Community discussion in ehrbase/openEHR_SDK#24 (2020) shows Python client libraries were requested but never developed.

## Decision

We will use **httpx directly** to interact with the EHRBase REST API, implementing a lightweight custom `EHRBaseClient` wrapper class.

### Architecture

```
api/src/ehrbase/
├── client.py         # EHRBaseClient - thin wrapper around httpx
├── compositions.py   # Composition building helpers
├── queries.py        # AQL query templates and builders
└── templates.py      # Template management utilities
```

### API Coverage

| Operation | Endpoint | Method |
|-----------|----------|--------|
| Create EHR | `/openehr/v1/ehr` | POST/PUT |
| Get EHR | `/openehr/v1/ehr/{ehr_id}` | GET |
| Create Composition | `/openehr/v1/ehr/{ehr_id}/composition` | POST |
| Get Composition | `/openehr/v1/ehr/{ehr_id}/composition/{uid}` | GET |
| Delete Composition | `/openehr/v1/ehr/{ehr_id}/composition/{uid}` | DELETE |
| AQL Query | `/openehr/v1/query/aql` | POST |
| List Templates | `/openehr/v1/definition/template/adl1.4` | GET |
| Upload Template | `/openehr/v1/definition/template/adl1.4` | POST |

## Consequences

### Positive

- Minimal dependencies (only httpx, already used)
- Full control over request/response cycle
- Easy debugging with clear request/response logs
- Type-safe with Python type hints throughout
- Educational value: learn the openEHR API directly
- ~150 lines of client code vs thousands in an SDK

### Negative

- Must implement each endpoint method ourselves
- No validation helpers for FLAT compositions
- AQL queries are string-based with no type-safe builder
- Must manually map template paths
- Must keep up with EHRBase API changes

### Migration Path

If a Python SDK emerges in the future, our service layer already abstracts EHRBase calls, making incremental migration straightforward.

!!! note "Update: oehrpy"
    This decision directly led to the creation of [oehrpy](../oehrpy/index.md), a Python SDK for openEHR. See [PRD-0005](https://github.com/platzhersh/open-cis/blob/main/docs/prd/0005-oehrpy-sdk-integration.md) for the integration plan.
