# PRD-0005: oehrpy SDK Integration

**Version:** 1.0
**Date:** 2026-01-31
**Status:** Draft
**Owner:** Open CIS Project

---

## Executive Summary

Integrate **oehrpy v0.1.0**, our newly published Python openEHR SDK, into the Open CIS backend to replace raw HTTP calls and manual JSON construction with type-safe, validated composition building. This integration will serve as both a real-world validation of oehrpy and a significant improvement to Open CIS's code quality, maintainability, and developer experience.

**Key Benefits:**
- Type-safe composition building with full IDE autocomplete
- Validated RM objects via Pydantic models (134 classes)
- Simplified EHRBase integration via async REST client
- Template-aware builders (VitalSignsBuilder) for common use cases
- Elimination of raw JSON construction and path string errors

---

## Problem Statement

### Current Pain Points

**1. Manual JSON Construction is Error-Prone**

Open CIS currently builds openEHR compositions by manually constructing nested JSON structures:

```python
# Current approach - brittle, no type safety
flat_data = {
    "ctx/language": "en",
    "vital_signs/blood_pressure:0/any_event:0/systolic|magnitude": 120,
    "vital_signs/blood_pressure:0/any_event:0/systolic|unit": "mm[Hg]",
    # ... more paths prone to typos
}
```

This approach has caused us significant debugging time (documented in `docs/FLAT_FORMAT_VERSIONS.md`) when paths didn't match what EHRBase 2.26.0 expects.

**2. No Validation Until Runtime**

Composition errors are only caught when EHRBase returns HTTP 422. There's no way to catch invalid structures, missing required fields, or type mismatches before API calls.

**3. Duplicated Knowledge**

FLAT path structures, RM type definitions, and EHRBase API patterns are scattered across multiple service files. Changes to templates require updates in multiple places.

**4. Limited IDE Support**

Without typed models, developers get no autocomplete, no type checking, and no inline documentation when building clinical data structures.

### User Personas Affected

1. **Open CIS Developer** - Spends time debugging path errors instead of building features
2. **Clinical Informaticist** - Cannot easily understand code that maps UI to openEHR structures
3. **Contributor** - High barrier to entry for understanding openEHR integration patterns

---

## Goals & Success Metrics

### Goals

| Priority | Goal | Rationale |
|----------|------|-----------|
| P0 | Replace manual FLAT construction with VitalSignsBuilder | Eliminate path string errors, enable IDE support |
| P0 | Use EHRBaseClient for all CDR operations | Single, tested integration point |
| P1 | Validate compositions before EHRBase submission | Catch errors early, improve DX |
| P1 | Validate oehrpy in production use | Identify gaps, inform SDK roadmap |
| P2 | Demonstrate SDK value to openEHR community | Support article series, encourage adoption |

### Success Metrics

| Metric | Current | Target | How to Measure |
|--------|---------|--------|----------------|
| Lines of EHRBase integration code | ~150+ | <50 | Count LOC in `ehrbase/` module |
| Time to debug composition errors | Hours | Minutes | Developer experience feedback |
| Type coverage in clinical data layer | 0% | 100% | mypy strict mode pass |
| Runtime composition validation errors | Unknown | Logged | Add metrics endpoint |
| SDK issues discovered | 0 | Track all | GitHub issues on oehrpy |

---

## Scope

### In Scope (v1.0)

1. **Install oehrpy as dependency**
   - Add `oehrpy>=0.1.0` to `api/pyproject.toml`
   - Verify compatibility with Python 3.11+ and existing dependencies

2. **Replace EHRBase HTTP client**
   - Migrate from raw `httpx` calls to `openehr_sdk.client.EHRBaseClient`
   - Update `api/src/ehrbase/client.py` to wrap or replace with oehrpy client
   - Maintain async compatibility

3. **Refactor vital signs composition building**
   - Replace manual FLAT construction with `VitalSignsBuilder`
   - Update `api/src/services/vital_signs.py` (if exists) or create
   - Maintain backward-compatible API responses

4. **Add RM types for API responses**
   - Use oehrpy RM classes for serialization where appropriate
   - Improve API schema documentation with proper types

5. **Integration testing**
   - Add tests that validate oehrpy compositions against local EHRBase
   - Test VitalSignsBuilder output matches expected FLAT format

### Out of Scope (Future)

- **OPT Parser integration** - Generate new template builders from OPT files
- **AQL Builder adoption** - Replace raw AQL strings with fluent builder
- **Canonical JSON support** - Only FLAT format for now
- **Frontend SDK** - TypeScript/Vue integration remains manual
- **Additional template builders** - Only VitalSignsBuilder for now

---

## Technical Design

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    Open CIS API (FastAPI)                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────┐    ┌──────────────────────────────────┐   │
│  │  Routers        │    │  Services                        │   │
│  │  (unchanged)    │───▶│  vital_signs.py                  │   │
│  └─────────────────┘    │  encounters.py                   │   │
│                         │  patients.py                     │   │
│                         └──────────────┬───────────────────┘   │
│                                        │                        │
│                         ┌──────────────▼───────────────────┐   │
│                         │  oehrpy Integration Layer        │   │
│                         │                                  │   │
│                         │  ┌────────────────────────────┐  │   │
│                         │  │ VitalSignsBuilder          │  │   │
│                         │  │ - Type-safe composition    │  │   │
│                         │  │ - FLAT format output       │  │   │
│                         │  └────────────────────────────┘  │   │
│                         │                                  │   │
│                         │  ┌────────────────────────────┐  │   │
│                         │  │ EHRBaseClient (async)      │  │   │
│                         │  │ - EHR CRUD                 │  │   │
│                         │  │ - Composition CRUD         │  │   │
│                         │  │ - Template management      │  │   │
│                         │  │ - AQL queries              │  │   │
│                         │  └────────────────────────────┘  │   │
│                         │                                  │   │
│                         │  ┌────────────────────────────┐  │   │
│                         │  │ RM Classes (Pydantic)      │  │   │
│                         │  │ - DV_QUANTITY, DV_TEXT...  │  │   │
│                         │  │ - COMPOSITION, OBSERVATION │  │   │
│                         │  │ - Full validation          │  │   │
│                         │  └────────────────────────────┘  │   │
│                         └──────────────┬───────────────────┘   │
│                                        │                        │
└────────────────────────────────────────┼────────────────────────┘
                                         │ REST API
                        ┌────────────────▼────────────────┐
                        │           EHRBase               │
                        │    (openEHR CDR - Docker)       │
                        └─────────────────────────────────┘
```

### Dependency Addition

**File:** `api/pyproject.toml`

```toml
[project]
dependencies = [
    "fastapi>=0.109.0",
    "uvicorn>=0.27.0",
    "httpx>=0.26.0",
    "pydantic>=2.0.0",
    "prisma>=0.12.0",
    "oehrpy>=0.1.0",  # NEW: Python openEHR SDK
]
```

### Module Structure

```
api/src/
├── ehrbase/
│   ├── __init__.py
│   ├── client.py          # Wrap or replace with EHRBaseClient
│   ├── templates.py       # Template registration (unchanged)
│   └── config.py          # EHRBase connection settings
├── openehr/               # NEW: oehrpy integration layer
│   ├── __init__.py
│   ├── compositions.py    # Composition building helpers
│   └── queries.py         # AQL query helpers (future)
├── services/
│   ├── patient_service.py
│   ├── encounter_service.py
│   └── vital_signs_service.py  # Uses oehrpy builders
└── schemas/
    └── vital_signs.py     # API schemas (may use RM types)
```

### Code Examples

#### Before: Manual FLAT Construction

```python
# api/src/services/vital_signs.py (CURRENT)

async def create_vital_signs(
    ehr_id: str,
    systolic: float,
    diastolic: float,
    pulse: float,
    composer: str,
    recorded_at: datetime,
) -> str:
    """Create vital signs composition - manual JSON construction."""

    # Fragile: path strings can have typos, no validation
    flat_data = {
        "ctx/language": "en",
        "ctx/territory": "US",
        "ctx/composer_name": composer,
        "ctx/time": recorded_at.isoformat(),
        "vital_signs_observations/vital_signs/blood_pressure/systolic|magnitude": systolic,
        "vital_signs_observations/vital_signs/blood_pressure/systolic|unit": "mm[Hg]",
        "vital_signs_observations/vital_signs/blood_pressure/diastolic|magnitude": diastolic,
        "vital_signs_observations/vital_signs/blood_pressure/diastolic|unit": "mm[Hg]",
        "vital_signs_observations/vital_signs/blood_pressure/time": recorded_at.isoformat(),
        "vital_signs_observations/vital_signs/pulse_heart_beat/rate|magnitude": pulse,
        "vital_signs_observations/vital_signs/pulse_heart_beat/rate|unit": "/min",
        "vital_signs_observations/vital_signs/pulse_heart_beat/time": recorded_at.isoformat(),
    }

    # Raw HTTP call
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{EHRBASE_URL}/ehr/{ehr_id}/composition",
            json=flat_data,
            headers={
                "Content-Type": "application/openehr.flat+json",
                "Accept": "application/json",
            },
            auth=(EHRBASE_USER, EHRBASE_PASS),
        )
        response.raise_for_status()
        return response.json()["compositionUid"]
```

#### After: oehrpy VitalSignsBuilder

```python
# api/src/services/vital_signs.py (NEW)

from datetime import datetime
from openehr_sdk.templates import VitalSignsBuilder
from openehr_sdk.client import EHRBaseClient


async def create_vital_signs(
    ehr_id: str,
    systolic: float,
    diastolic: float,
    pulse: float,
    composer: str,
    recorded_at: datetime | None = None,
) -> str:
    """Create vital signs composition using oehrpy SDK.

    Type-safe, validated, with full IDE support.
    """
    recorded_at = recorded_at or datetime.now()

    # Type-safe builder with IDE autocomplete
    builder = VitalSignsBuilder(
        composer_name=composer,
        start_time=recorded_at,
        language="en",
        territory="US",
    )

    # Fluent API - impossible to use wrong paths
    builder.add_blood_pressure(
        systolic=systolic,
        diastolic=diastolic,
        time=recorded_at,
    )
    builder.add_pulse(
        rate=pulse,
        time=recorded_at,
    )

    # Build validated FLAT format
    flat_data = builder.build()

    # Async client handles auth, headers, error handling
    async with EHRBaseClient(
        base_url=settings.ehrbase_url,
        username=settings.ehrbase_user,
        password=settings.ehrbase_password,
    ) as client:
        composition_uid = await client.create_composition(
            ehr_id=ehr_id,
            template_id=VitalSignsBuilder.template_id,
            composition=flat_data,
            format="flat",
        )
        return composition_uid
```

#### EHRBase Client Integration

```python
# api/src/ehrbase/client.py (REFACTORED)

from openehr_sdk.client import EHRBaseClient as OehrpyClient
from contextlib import asynccontextmanager


class EHRBaseService:
    """Open CIS EHRBase integration using oehrpy SDK."""

    def __init__(self, settings):
        self.settings = settings
        self._client: OehrpyClient | None = None

    @asynccontextmanager
    async def client(self):
        """Get async EHRBase client."""
        if self._client is None:
            self._client = OehrpyClient(
                base_url=self.settings.ehrbase_url,
                username=self.settings.ehrbase_user,
                password=self.settings.ehrbase_password,
            )
        async with self._client:
            yield self._client

    async def create_ehr(self) -> str:
        """Create a new EHR, return ehr_id."""
        async with self.client() as client:
            ehr = await client.create_ehr()
            return ehr.ehr_id

    async def get_ehr(self, ehr_id: str):
        """Get EHR by ID."""
        async with self.client() as client:
            return await client.get_ehr(ehr_id)

    async def execute_aql(self, query: str, params: dict | None = None):
        """Execute AQL query."""
        async with self.client() as client:
            return await client.execute_aql(query, params or {})
```

### Configuration

**File:** `api/src/config.py`

```python
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql://..."

    # EHRBase (oehrpy client configuration)
    ehrbase_url: str = "http://localhost:8080/ehrbase/rest"
    ehrbase_user: str = "admin"
    ehrbase_password: str = "admin"

    # oehrpy SDK options
    ehrbase_timeout: float = 30.0  # Request timeout in seconds
    ehrbase_verify_ssl: bool = True

    class Config:
        env_file = ".env"


settings = Settings()
```

---

## Migration Plan

### Phase 1: Installation & Verification (Day 1)

1. Add oehrpy to dependencies
2. Run existing tests to verify no conflicts
3. Create simple integration test with EHRBaseClient

```python
# tests/test_oehrpy_integration.py

import pytest
from openehr_sdk.client import EHRBaseClient
from openehr_sdk.templates import VitalSignsBuilder


@pytest.mark.asyncio
async def test_ehrbase_client_connection():
    """Verify oehrpy client can connect to EHRBase."""
    async with EHRBaseClient(
        base_url="http://localhost:8080/ehrbase/rest",
        username="admin",
        password="admin",
    ) as client:
        status = await client.get_status()
        assert status["status"] == "UP"


@pytest.mark.asyncio
async def test_vital_signs_builder_produces_valid_flat():
    """Verify VitalSignsBuilder output matches expected format."""
    builder = VitalSignsBuilder(composer_name="Test")
    builder.add_blood_pressure(systolic=120, diastolic=80)
    builder.add_pulse(rate=72)

    flat = builder.build()

    # Verify structure
    assert "vital_signs_observations" in str(flat)
    assert flat.get("vital_signs_observations/vital_signs/blood_pressure/systolic|magnitude") == 120
```

### Phase 2: Client Migration (Day 2-3)

1. Create `EHRBaseService` wrapper class
2. Update `create_ehr` in patient service
3. Update `execute_aql` in query endpoints
4. Run integration tests

### Phase 3: Composition Builder Migration (Day 4-5)

1. Refactor vital signs creation to use `VitalSignsBuilder`
2. Update any composition reading to use oehrpy deserialization
3. Add new tests for composition round-trip
4. Manual testing of vital signs recording flow

### Phase 4: Cleanup & Documentation (Day 6)

1. Remove deprecated raw HTTP code
2. Update API documentation
3. Update CONTEXT.md with oehrpy usage patterns
4. Create ADR for oehrpy adoption decision

---

## API Changes

### No Breaking Changes

The external API remains identical. Changes are internal implementation only.

**Existing Endpoint (unchanged):**

```http
POST /api/patients/{patient_id}/vital-signs
Content-Type: application/json

{
  "systolic": 120,
  "diastolic": 80,
  "pulse": 72,
  "recorded_at": "2026-01-31T10:30:00Z"
}
```

**Response (unchanged):**

```json
{
  "id": "uuid",
  "composition_uid": "f47ac10b-58cc-4372-a567-0e02b2c3d479::open-cis::1",
  "systolic": 120,
  "diastolic": 80,
  "pulse": 72,
  "recorded_at": "2026-01-31T10:30:00Z"
}
```

### Internal Schema Improvements (Optional)

Where appropriate, API schemas may be enhanced with oehrpy types:

```python
# api/src/schemas/vital_signs.py

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class VitalSignsCreate(BaseModel):
    """Request schema for recording vital signs."""
    systolic: float = Field(..., ge=0, le=300, description="Systolic BP in mmHg")
    diastolic: float = Field(..., ge=0, le=200, description="Diastolic BP in mmHg")
    pulse: Optional[float] = Field(None, ge=0, le=300, description="Pulse rate in /min")
    temperature: Optional[float] = Field(None, description="Body temp in °C")
    recorded_at: Optional[datetime] = Field(None, description="When vitals were recorded")


class VitalSignsResponse(BaseModel):
    """Response schema including openEHR metadata."""
    id: str
    composition_uid: str
    systolic: float
    diastolic: float
    pulse: Optional[float]
    temperature: Optional[float]
    recorded_at: datetime

    # Optional: openEHR transparency (from PRD-0004)
    openehr_metadata: Optional[dict] = Field(
        None,
        description="openEHR composition metadata for transparency"
    )
```

---

## Testing Strategy

### Unit Tests

```python
# tests/unit/test_vital_signs_builder.py

def test_builder_creates_required_fields():
    """VitalSignsBuilder includes all required FLAT fields."""
    builder = VitalSignsBuilder(composer_name="Dr. Smith")
    flat = builder.build()

    # Required context fields
    assert "vital_signs_observations/category|code" in flat
    assert "vital_signs_observations/composer|name" in flat
    assert "vital_signs_observations/context/start_time" in flat


def test_builder_blood_pressure_paths():
    """Blood pressure uses correct EHRBase 2.26+ FLAT paths."""
    builder = VitalSignsBuilder(composer_name="Test")
    builder.add_blood_pressure(systolic=120, diastolic=80)
    flat = builder.build()

    # Verify new format (no :0 indices for single observations)
    assert flat["vital_signs_observations/vital_signs/blood_pressure/systolic|magnitude"] == 120
    assert flat["vital_signs_observations/vital_signs/blood_pressure/diastolic|magnitude"] == 80


def test_builder_rejects_invalid_values():
    """Builder validates inputs before building."""
    builder = VitalSignsBuilder(composer_name="Test")

    with pytest.raises(ValueError):
        builder.add_blood_pressure(systolic=-10, diastolic=80)  # Negative systolic
```

### Integration Tests

```python
# tests/integration/test_ehrbase_composition.py

@pytest.mark.asyncio
async def test_create_and_retrieve_vital_signs():
    """Full round-trip: create composition, query back."""
    # Create
    builder = VitalSignsBuilder(composer_name="Integration Test")
    builder.add_blood_pressure(systolic=125, diastolic=82)
    builder.add_pulse(rate=68)

    async with EHRBaseClient(...) as client:
        # Create EHR
        ehr = await client.create_ehr()

        # Commit composition
        uid = await client.create_composition(
            ehr_id=ehr.ehr_id,
            template_id=VitalSignsBuilder.template_id,
            composition=builder.build(),
            format="flat",
        )

        # Verify via AQL
        results = await client.execute_aql(
            """
            SELECT c/uid/value,
                   o/data[at0001]/events[at0006]/data[at0003]/items[at0004]/value/magnitude as systolic
            FROM EHR e
            CONTAINS COMPOSITION c
            CONTAINS OBSERVATION o[openEHR-EHR-OBSERVATION.blood_pressure.v1]
            WHERE e/ehr_id/value = :ehr_id
            """,
            {"ehr_id": ehr.ehr_id}
        )

        assert len(results) == 1
        assert results[0]["systolic"] == 125
```

### E2E Tests

```python
# tests/e2e/test_vital_signs_api.py

@pytest.mark.asyncio
async def test_record_vital_signs_e2e(client, test_patient):
    """End-to-end: API → oehrpy → EHRBase → AQL → API."""
    response = await client.post(
        f"/api/patients/{test_patient.id}/vital-signs",
        json={
            "systolic": 118,
            "diastolic": 76,
            "pulse": 72,
        }
    )

    assert response.status_code == 201
    data = response.json()
    assert data["systolic"] == 118
    assert "composition_uid" in data

    # Verify can retrieve
    get_response = await client.get(
        f"/api/patients/{test_patient.id}/vital-signs"
    )
    assert len(get_response.json()) >= 1
```

---

## Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| oehrpy bugs discovered in production | Medium | Medium | Comprehensive tests, fallback to raw HTTP if critical |
| EHRBase version incompatibility | Low | High | Pin EHRBase version, test against CI container |
| Performance regression | Low | Medium | Benchmark before/after, async throughout |
| Breaking changes in oehrpy 0.2.0 | Medium | Low | Pin to 0.1.x, review changelog before updates |
| Learning curve for contributors | Medium | Low | Document patterns, add examples |

---

## Open Questions

### Question 1: Should we fully replace httpx or wrap EHRBaseClient?

**Options:**
- A) **Full replacement** - Remove all raw httpx, use only EHRBaseClient
- B) **Wrapper pattern** - Keep EHRBaseService that delegates to oehrpy client
- C) **Gradual migration** - Use both, migrate endpoint by endpoint

**Decision:** Option B (Wrapper pattern) - Maintains flexibility to extend behavior, add logging/metrics, and potentially swap implementations.

### Question 2: How to handle oehrpy client lifecycle in FastAPI?

**Options:**
- A) Create new client per request
- B) Singleton client with connection pooling
- C) Dependency injection via FastAPI `Depends()`

**Decision:** Option C - Aligns with FastAPI patterns, enables testing via overrides.

```python
# Example dependency injection
async def get_ehrbase_client() -> AsyncGenerator[EHRBaseClient, None]:
    async with EHRBaseClient(...) as client:
        yield client

@router.post("/vital-signs")
async def create_vital_signs(
    data: VitalSignsCreate,
    client: EHRBaseClient = Depends(get_ehrbase_client),
):
    ...
```

### Question 3: Should API responses include oehrpy RM objects?

**Options:**
- A) Keep current dict responses, no RM types in API
- B) Serialize RM objects directly for internal APIs
- C) Create separate "raw" endpoints that return RM structures

**Decision:** Option A for now, consider C later for admin interface (PRD-0001).

---

## Dependencies

### Python Packages

| Package | Version | Purpose |
|---------|---------|---------|
| oehrpy | >=0.1.0 | Python openEHR SDK |
| httpx | >=0.26.0 | Already present (oehrpy uses internally) |
| pydantic | >=2.0.0 | Already present (oehrpy uses for RM models) |

### Infrastructure

- **EHRBase 2.26.0+** - Required for FLAT format compatibility
- **Docker Compose** - Local development (unchanged)

---

## Success Criteria

**The integration is successful when:**

- ✅ All existing tests pass with oehrpy integration
- ✅ Vital signs creation uses VitalSignsBuilder exclusively
- ✅ EHRBase client operations use oehrpy EHRBaseClient
- ✅ mypy passes with strict mode on clinical data layer
- ✅ No raw FLAT path strings in service layer code
- ✅ Integration tests verify composition round-trip
- ✅ Manual testing confirms vital signs flow works end-to-end
- ✅ Performance is comparable or better than raw HTTP

---

## Appendix A: oehrpy 0.1.0 Feature Matrix

| Feature | Status | Notes |
|---------|--------|-------|
| RM Classes (134 types) | ✅ Available | Pydantic v2 models |
| FLAT Serialization | ✅ Available | EHRBase 2.26.0+ format |
| Canonical JSON | ✅ Available | Full round-trip support |
| EHRBase Client | ✅ Available | Async, all REST endpoints |
| VitalSignsBuilder | ✅ Available | IDCR template support |
| OPT Parser | ✅ Available | Parse OPT 1.4 XML |
| Template Generator | ✅ Available | Generate builders from OPT |
| AQL Builder | ✅ Available | Fluent query API |

---

## Appendix B: Related Documents

- [PRD-0004: Vital Signs Chart](./0004-vital-signs-chart.md) - UI for vital signs
- [ADR-0001: Template Management](../adr/0001-openehr-template-management.md) - Template registration
- [FLAT Format Versions](../FLAT_FORMAT_VERSIONS.md) - Format documentation gap
- [oehrpy README](https://github.com/platzhersh/oehrpy) - SDK documentation
- [Open CIS Part 3: Architecture](../../open-cis-part3-architecture.md) - Current integration patterns
- [Open CIS Part 4: SDK Landscape](../../open-cis-part4-sdk-landscape.md) - Why we built oehrpy

---

## Change Log

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-01-31 | Open CIS Team | Initial PRD draft |
