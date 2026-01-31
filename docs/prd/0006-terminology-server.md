# PRD-0006: FHIR Terminology Server Integration

**Status:** Draft
**Author:** Chregi / Open CIS Team
**Created:** 2026-01-31
**Priority:** P1 (Should Have)
**Inspired by:** [Ian McNicoll's feedback on openEHR Discourse](https://discourse.openehr.org/t/building-an-open-cis-article-series-on-implementing-a-minimal-cis-with-ehrbase/11690)

---

## Executive Summary

Integrate a FHIR Terminology Server with Open CIS to provide standardized clinical terminology services. This enables code validation, searchable terminology lookups, value set expansion, and code translation—essential capabilities for any clinical system handling coded data like diagnoses (ICD-10), procedures (SNOMED CT), and lab tests (LOINC).

**Why now?** Open CIS can store clinical data via EHRBase, but lacks the ability to validate or browse the terminology codes referenced in that data. A terminology server bridges this gap, transforming Open CIS from a data store into a clinically useful application.

---

## Problem Statement

### Current State

Open CIS stores compositions in EHRBase using openEHR's rich data model, including `DV_CODED_TEXT` elements that reference external terminologies (SNOMED CT, ICD-10, LOINC). However:

1. **No code validation** — Users can enter invalid or deprecated codes without warning
2. **No searchable code picker** — Users must know exact codes; no autocomplete or browsing
3. **No value set expansion** — Templates reference value sets, but we can't resolve them to actual codes
4. **No code translation** — Cannot map between terminologies (e.g., SNOMED → ICD-10 for billing)
5. **No hierarchy navigation** — Cannot leverage SNOMED CT's rich hierarchical relationships

### Impact

- **Data quality issues** — Invalid codes pollute the clinical data repository
- **Poor user experience** — Clinicians must manually look up codes in external references
- **Limited interoperability** — Cannot participate in terminology-aware data exchange
- **Template constraints ignored** — Value set bindings in templates are not enforced

---

## Solution Overview

Deploy a FHIR Terminology Server alongside EHRBase and integrate it with the Open CIS application layer. The terminology server provides a standardized FHIR API for:

- **Code validation** (`$validate-code`)
- **Code lookup** (`$lookup`)
- **Value set expansion** (`$expand`)
- **Subsumption testing** (`$subsumes`)
- **Code translation** (`$translate`)
- **ECL query execution** (SNOMED CT Expression Constraint Language)

### Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Open CIS Frontend                           │
│                           (Vue 3 + TypeScript)                      │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────┐ │
│  │  Code Picker    │  │ Validation UI   │  │ Terminology Browser │ │
│  │  Components     │  │ Feedback        │  │ (optional)          │ │
│  └────────┬────────┘  └────────┬────────┘  └──────────┬──────────┘ │
└───────────┼─────────────────────┼─────────────────────┼────────────┘
            │                     │                     │
            ▼                     ▼                     ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         Open CIS Backend                            │
│                           (FastAPI + Python)                        │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                  Terminology Service Layer                   │   │
│  │  • TerminologyClient (FHIR API wrapper)                     │   │
│  │  • CodeValidator                                             │   │
│  │  • ValueSetResolver                                          │   │
│  │  • TerminologyCache (Redis/in-memory)                       │   │
│  └────────────────────────┬────────────────────────────────────┘   │
│                           │                                         │
│  ┌────────────────────────┼────────────────────────────────────┐   │
│  │         EHRBase        │      FHIR Terminology Server       │   │
│  │         Client         │           Client                   │   │
│  └───────────┬────────────┴──────────────┬─────────────────────┘   │
└──────────────┼───────────────────────────┼─────────────────────────┘
               │                           │
               ▼                           ▼
┌──────────────────────────┐  ┌─────────────────────────────────────┐
│        EHRBase           │  │     FHIR Terminology Server         │
│    (Clinical Data)       │  │   (Snowstorm Lite / HAPI FHIR)      │
│                          │  │                                     │
│  • Compositions          │  │  • SNOMED CT                        │
│  • Templates             │  │  • ICD-10                           │
│  • AQL Queries           │  │  • LOINC                            │
│                          │  │  • Custom ValueSets                 │
└──────────────────────────┘  └─────────────────────────────────────┘
```

---

## Functional Requirements

### Phase 1: Infrastructure & Basic Integration (MVP)

**Priority:** P0 (Must Have)

#### 1.1 Terminology Server Deployment

**User Story:** As a developer, I want to run a FHIR terminology server locally so I can develop terminology features.

**Requirements:**

- Add Snowstorm Lite to `docker-compose.yml` as a new service
- Configure persistent volume for terminology index data
- Document SNOMED CT license requirements and data loading process
- Provide script to load SNOMED CT International Edition
- Health check endpoint integration with existing startup scripts
- Environment variable configuration for terminology server URL

**Technical Notes:**

```yaml
# docker-compose.yml addition
terminology-server:
  image: snomedinternational/snowstorm-lite:latest
  ports:
    - "8081:8080"
  volumes:
    - terminology-data:/app/lucene-index
  environment:
    - INDEX_PATH=lucene-index/data
    - ADMIN_PASSWORD=${TERMINOLOGY_ADMIN_PASSWORD}
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost:8080/fhir/metadata"]
    interval: 30s
    timeout: 10s
    retries: 5
```

**Acceptance Criteria:**

- [ ] `docker-compose up` starts terminology server alongside EHRBase
- [ ] Terminology server responds to `/fhir/metadata` (CapabilityStatement)
- [ ] SNOMED CT data can be loaded via documented process
- [ ] Server survives container restarts (persistent index)

#### 1.2 Terminology Client Library

**User Story:** As a backend developer, I want a Python client for FHIR terminology operations so I can integrate terminology services into the API.

**Requirements:**

- Create `api/src/terminology/client.py` with async FHIR client
- Implement core operations: `$lookup`, `$validate-code`, `$expand`
- Handle FHIR R4 response parsing
- Implement connection pooling and timeout handling
- Add retry logic for transient failures
- Create Pydantic models for terminology responses

**API Design:**

```python
# api/src/terminology/client.py

from typing import Optional, List
from pydantic import BaseModel
import httpx

class CodeLookupResult(BaseModel):
    code: str
    system: str
    display: str
    version: Optional[str] = None
    properties: dict = {}

class ValidationResult(BaseModel):
    valid: bool
    message: Optional[str] = None
    display: Optional[str] = None

class ValueSetExpansion(BaseModel):
    url: str
    total: int
    contains: List[CodeLookupResult]

class TerminologyClient:
    """Async client for FHIR Terminology Server operations."""

    def __init__(self, base_url: str, timeout: float = 30.0):
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None

    async def lookup(
        self,
        system: str,
        code: str,
        properties: Optional[List[str]] = None
    ) -> CodeLookupResult:
        """
        Look up a code and return its display name and properties.

        FHIR Operation: CodeSystem/$lookup
        """
        pass

    async def validate_code(
        self,
        system: str,
        code: str,
        display: Optional[str] = None,
        value_set_url: Optional[str] = None
    ) -> ValidationResult:
        """
        Validate that a code exists and optionally belongs to a value set.

        FHIR Operation: CodeSystem/$validate-code or ValueSet/$validate-code
        """
        pass

    async def expand_value_set(
        self,
        url: str,
        filter: Optional[str] = None,
        count: int = 100,
        offset: int = 0
    ) -> ValueSetExpansion:
        """
        Expand a value set to get all contained codes.

        FHIR Operation: ValueSet/$expand
        """
        pass

    async def subsumes(
        self,
        system: str,
        code_a: str,
        code_b: str
    ) -> str:
        """
        Test subsumption relationship between two codes.

        Returns: 'equivalent', 'subsumes', 'subsumed-by', or 'not-subsumed'

        FHIR Operation: CodeSystem/$subsumes
        """
        pass
```

**Acceptance Criteria:**

- [ ] Client can connect to Snowstorm Lite and perform all core operations
- [ ] All operations have corresponding Pydantic response models
- [ ] Timeout and retry behavior is configurable
- [ ] Unit tests with mocked responses achieve 90% coverage
- [ ] Integration tests pass against running Snowstorm Lite

#### 1.3 API Endpoints

**User Story:** As a frontend developer, I want REST endpoints for terminology operations so I can build terminology-aware UI components.

**Requirements:**

- Create `api/src/routers/terminology.py` router
- Expose terminology operations via REST endpoints
- Add OpenAPI documentation with examples
- Implement request validation and error handling

**Endpoint Design:**

```
GET  /api/terminology/lookup
     ?system=http://snomed.info/sct
     &code=73211009
     → Returns code details (display, properties)

GET  /api/terminology/validate
     ?system=http://snomed.info/sct
     &code=73211009
     &valueset=http://example.org/fhir/ValueSet/diagnoses
     → Returns validation result

GET  /api/terminology/expand
     ?url=http://snomed.info/sct?fhir_vs=ecl/<73211009
     &filter=diabetes
     &count=20
     → Returns matching codes from value set

GET  /api/terminology/search
     ?system=http://snomed.info/sct
     &term=diabetes
     &count=20
     → Returns codes matching search term
```

**Acceptance Criteria:**

- [ ] All endpoints documented in OpenAPI spec
- [ ] Error responses follow existing API patterns
- [ ] Response times < 500ms for typical operations
- [ ] Rate limiting applied to prevent abuse

---

### Phase 2: Form Integration

**Priority:** P1 (Should Have)

#### 2.1 Code Picker Component

**User Story:** As a clinician, I want to search for diagnosis codes while entering data so I don't have to memorize SNOMED CT codes.

**Requirements:**

- Create `CodePicker.vue` component for searching/selecting codes
- Support typeahead search with debouncing
- Display code, display name, and system
- Support binding to specific value sets (from template constraints)
- Show loading states and error handling
- Keyboard navigation support

**Component API:**

```vue
<template>
  <CodePicker
    v-model="selectedCode"
    :system="'http://snomed.info/sct'"
    :value-set-url="'http://example.org/fhir/ValueSet/diagnoses'"
    :placeholder="'Search diagnoses...'"
    :min-search-length="2"
    :debounce-ms="300"
    @search="handleSearch"
    @select="handleSelect"
  />
</template>

<script setup lang="ts">
interface CodedValue {
  code: string;
  system: string;
  display: string;
}

const selectedCode = ref<CodedValue | null>(null);
</script>
```

**Acceptance Criteria:**

- [ ] Search returns results within 500ms of typing pause
- [ ] Minimum 2 characters before search triggers
- [ ] Selected code persists in form state
- [ ] Works with keyboard-only navigation
- [ ] Accessible (ARIA labels, screen reader support)

#### 2.2 Vital Signs Integration

**User Story:** As a developer, I want the vital signs form to use terminology-backed code pickers where appropriate.

**Requirements:**

- Identify coded fields in IDCR Vital Signs template (e.g., body position, cuff size)
- Replace static dropdowns with CodePicker components bound to appropriate value sets
- Create value sets for non-SNOMED coded options if needed
- Validate coded values before composition submission

**Template Analysis:**

The IDCR Vital Signs template includes these coded fields suitable for terminology binding:

| Field | Current Implementation | Proposed ValueSet |
|-------|----------------------|-------------------|
| Blood Pressure / Position | Static dropdown | `openehr:position` (local) |
| Blood Pressure / Cuff Size | Static dropdown | SNOMED CT: descendants of 70665002 |
| Pulse / Body Site | Free text | SNOMED CT: ECL `<< 442083009` |
| Temperature / Body Site | Free text | SNOMED CT: body structure subset |

**Acceptance Criteria:**

- [ ] At least 2 coded fields use terminology-backed picker
- [ ] Value sets defined and loaded into terminology server
- [ ] Form submission validates codes against terminology server
- [ ] Fallback to static dropdown if terminology server unavailable

---

### Phase 3: Validation & Data Quality

**Priority:** P2 (Nice to Have)

#### 3.1 Composition Validation Hook

**User Story:** As a data steward, I want compositions validated against terminology before storage so invalid codes don't pollute the CDR.

**Requirements:**

- Create validation middleware for composition submissions
- Extract all `DV_CODED_TEXT` values from FLAT format
- Validate each code against terminology server
- Return detailed validation errors with suggestions
- Make validation configurable (strict/warn/off)

**Validation Flow:**

```
Composition Submit Request
         │
         ▼
┌────────────────────────┐
│  Extract Coded Values  │
│  from FLAT format      │
└───────────┬────────────┘
            │
            ▼
┌────────────────────────┐
│  Batch Validate Codes  │  ◄── Parallel requests to terminology server
│  against terminology   │
└───────────┬────────────┘
            │
      ┌─────┴─────┐
      │           │
   Valid?      Invalid
      │           │
      ▼           ▼
┌──────────┐  ┌────────────────┐
│ Forward  │  │ Return errors  │
│ to       │  │ with invalid   │
│ EHRBase  │  │ code details   │
└──────────┘  └────────────────┘
```

**Acceptance Criteria:**

- [ ] All `DV_CODED_TEXT` values extracted from FLAT compositions
- [ ] Validation results include code, expected system, and error message
- [ ] Batch validation completes within 2 seconds for typical compositions
- [ ] Configuration flag to enable/disable validation

#### 3.2 Code Translation Service

**User Story:** As a system integrator, I want to translate SNOMED CT codes to ICD-10 for billing purposes.

**Requirements:**

- Expose `$translate` operation via API
- Load SNOMED CT to ICD-10 map into terminology server
- Handle one-to-many and approximate mappings
- Return mapping metadata (equivalence type, comments)

**Acceptance Criteria:**

- [ ] Can translate SNOMED CT diagnoses to ICD-10-CM
- [ ] API returns all possible mappings with confidence levels
- [ ] Mappings sourced from official SNOMED International maps

---

### Phase 4: Advanced Features (Future)

**Priority:** P3 (Future Consideration)

#### 4.1 Terminology Browser UI

A standalone page for browsing terminology content:

- Hierarchical tree view for SNOMED CT
- Search across all loaded code systems
- View concept details, relationships, and mappings
- ECL query builder for advanced searches

#### 4.2 Custom Value Set Management

Allow administrators to create and manage custom value sets:

- Define value sets using ECL or explicit code lists
- Version and publish value sets
- Bind value sets to template fields via configuration

#### 4.3 Terminology Syndication

Automatically keep terminology content up to date:

- Subscribe to SNOMED CT release feeds
- Automated loading of new versions
- Version comparison and migration tools

---

## Technical Specifications

### Terminology Server Selection

| Server | License | SNOMED Support | Docker | Memory | Recommendation |
|--------|---------|---------------|--------|--------|----------------|
| **Snowstorm Lite** | Apache 2.0 | Excellent (official) | Yes | 500MB | **MVP Choice** |
| Snowstorm (Full) | Apache 2.0 | Excellent | Yes | 8GB+ | Production scale |
| HAPI FHIR | Apache 2.0 | Good | Yes | 2GB+ | Multi-terminology |
| Ontoserver | Commercial | Excellent | Yes | 2GB+ | Enterprise |

**Recommendation:** Start with **Snowstorm Lite** for MVP. It's the official SNOMED International server, has minimal resource requirements, and provides all core FHIR terminology operations. Migrate to full Snowstorm or HAPI FHIR if multi-terminology support becomes critical.

### SNOMED CT Licensing

**Important:** SNOMED CT requires a license. Options:

1. **SNOMED International Member Country** — Free access if your country is a member (includes USA, UK, Australia, Germany, Switzerland, etc.)
2. **Affiliate License** — Apply via [SNOMED International MLDS](https://mlds.ihtsdotools.org/)
3. **Demo/Development** — Use the public Snowstorm instance for development only

For Open CIS as a learning project, use the public sandbox or apply for an affiliate license.

### System URIs

Standard FHIR terminology system identifiers:

```
SNOMED CT:     http://snomed.info/sct
ICD-10:        http://hl7.org/fhir/sid/icd-10
ICD-10-CM:     http://hl7.org/fhir/sid/icd-10-cm
LOINC:         http://loinc.org
RxNorm:        http://www.nlm.nih.gov/research/umls/rxnorm
UCUM:          http://unitsofmeasure.org
```

### Caching Strategy

Terminology lookups are expensive. Implement multi-level caching:

1. **In-memory LRU cache** — Most recent 1000 lookups (5 minute TTL)
2. **Redis cache** (optional) — Shared across API instances (1 hour TTL)
3. **HTTP caching** — Respect `Cache-Control` headers from terminology server

### Error Handling

Terminology server unavailability should not block clinical workflows:

| Scenario | Behavior |
|----------|----------|
| Server unreachable | Log warning, allow free-text entry, mark for later validation |
| Code not found | Return validation error with suggestion to check spelling |
| Value set not found | Fall back to full code system search |
| Timeout | Return cached result if available, otherwise degrade gracefully |

---

## Data Model Changes

### New Environment Variables

```bash
# .env additions
TERMINOLOGY_SERVER_URL=http://localhost:8081/fhir
TERMINOLOGY_SERVER_TIMEOUT=30
TERMINOLOGY_CACHE_TTL=300
TERMINOLOGY_VALIDATION_MODE=warn  # strict | warn | off
```

### New API Dependencies

```toml
# pyproject.toml additions
httpx = "^0.27.0"      # Async HTTP client for FHIR requests
cachetools = "^5.3.0"  # In-memory caching
```

---

## User Interface Mockups

### Code Picker Component

```
┌─────────────────────────────────────────────────────┐
│ Diagnosis                                           │
│ ┌─────────────────────────────────────────────────┐ │
│ │ 🔍 diabetes                              [×]    │ │
│ └─────────────────────────────────────────────────┘ │
│ ┌─────────────────────────────────────────────────┐ │
│ │ ○ 73211009 | Diabetes mellitus              ▼  │ │
│ │ ○ 44054006 | Type 2 diabetes mellitus          │ │
│ │ ○ 46635009 | Type 1 diabetes mellitus          │ │
│ │ ○ 11530004 | Gestational diabetes mellitus     │ │
│ │ ○ 237599002 | Diabetes mellitus in pregnancy   │ │
│ │   ─────────────────────────────────────────    │ │
│ │   Showing 5 of 127 results                     │ │
│ └─────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────┘
```

### Validation Error Display

```
┌─────────────────────────────────────────────────────┐
│ ⚠️ Validation Warning                               │
│                                                     │
│ The following codes could not be validated:         │
│                                                     │
│ • Blood Pressure / Position: "sittng"               │
│   Code not found in SNOMED CT                       │
│   Did you mean: 33586001 | Sitting position         │
│                                                     │
│ [Continue Anyway]              [Fix and Resubmit]   │
└─────────────────────────────────────────────────────┘
```

---

## Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Code lookup latency (P95) | < 500ms | API metrics |
| Search result relevance | Top 5 contains correct code 90% of time | User testing |
| Validation accuracy | 99% of valid codes pass, 95% of invalid codes fail | Test suite |
| Cache hit rate | > 80% after warm-up | Cache metrics |
| Code picker adoption | Used in 100% of coded fields | Code review |

---

## Implementation Plan

### Phase 1: Infrastructure (Week 1-2)

| Day | Task | Owner |
|-----|------|-------|
| 1-2 | Add Snowstorm Lite to docker-compose, document SNOMED loading | Dev |
| 3-4 | Implement TerminologyClient with core operations | Dev |
| 5 | Add unit tests with mocked responses | Dev |
| 6-7 | Create API endpoints, add integration tests | Dev |
| 8-10 | Documentation, code review, merge | Dev |

### Phase 2: Form Integration (Week 3-4)

| Day | Task | Owner |
|-----|------|-------|
| 1-3 | Build CodePicker Vue component | Dev |
| 4-5 | Add Storybook stories, accessibility testing | Dev |
| 6-7 | Integrate with vital signs form (2+ fields) | Dev |
| 8-10 | End-to-end testing, polish, merge | Dev |

### Phase 3: Validation (Week 5-6)

| Day | Task | Owner |
|-----|------|-------|
| 1-3 | Implement composition validation hook | Dev |
| 4-5 | Add validation UI feedback | Dev |
| 6-7 | Configuration and documentation | Dev |
| 8-10 | Testing, code review, merge | Dev |

---

## Risks and Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| SNOMED CT license complexity | Medium | High | Document process clearly; use public sandbox for dev |
| Terminology server adds latency | Medium | Medium | Aggressive caching; async validation |
| Snowstorm Lite limitations | Low | Medium | Clear migration path to full Snowstorm |
| Value set maintenance burden | Medium | Low | Start with standard value sets; defer custom ones |

---

## Open Questions

1. **Multi-terminology support** — Should MVP include ICD-10 and LOINC, or focus on SNOMED CT only?
   - *Recommendation:* SNOMED CT only for MVP; others in Phase 4

2. **Offline mode** — Should the system work without terminology server access?
   - *Recommendation:* Degrade gracefully; allow free-text with validation flag

3. **Value set authoring** — Who defines custom value sets, and where are they stored?
   - *Recommendation:* Defer to Phase 4; use ECL-based implicit value sets initially

4. **Version pinning** — How do we handle SNOMED CT version updates?
   - *Recommendation:* Pin to specific release in docker-compose; manual update process

---

## References

- [FHIR Terminology Services Specification](https://www.hl7.org/fhir/terminology-service.html)
- [Snowstorm Lite GitHub](https://github.com/IHTSDO/snowstorm-lite)
- [Snowstorm (Full) GitHub](https://github.com/IHTSDO/snowstorm)
- [SNOMED CT FHIR API Guide](https://docs.snomed.org/implementation-guides/snomed-ips-terminology-implementation-guide/3-using-a-terminology-server)
- [SNOMED CT Expression Constraint Language](https://confluence.ihtsdotools.org/display/DOCECL)
- [openEHR Discourse: Use of terminology service in CKM](https://discourse.openehr.org/t/use-of-a-terminology-service-in-ckm/3899)
- [Ian McNicoll's feedback thread](https://discourse.openehr.org/t/building-an-open-cis-article-series-on-implementing-a-minimal-cis-with-ehrbase/11690)

---

## Appendix A: FHIR Operations Quick Reference

### CodeSystem/$lookup

```http
GET /fhir/CodeSystem/$lookup?system=http://snomed.info/sct&code=73211009

Response:
{
  "resourceType": "Parameters",
  "parameter": [
    { "name": "name", "valueString": "SNOMED CT" },
    { "name": "display", "valueString": "Diabetes mellitus" },
    { "name": "property", "part": [
      { "name": "code", "valueCode": "inactive" },
      { "name": "valueBoolean", "valueBoolean": false }
    ]}
  ]
}
```

### ValueSet/$expand

```http
GET /fhir/ValueSet/$expand?url=http://snomed.info/sct?fhir_vs=ecl/<73211009&filter=type%202&count=10

Response:
{
  "resourceType": "ValueSet",
  "expansion": {
    "total": 47,
    "contains": [
      {
        "system": "http://snomed.info/sct",
        "code": "44054006",
        "display": "Type 2 diabetes mellitus"
      }
    ]
  }
}
```

### CodeSystem/$validate-code

```http
GET /fhir/CodeSystem/$validate-code?system=http://snomed.info/sct&code=73211009

Response:
{
  "resourceType": "Parameters",
  "parameter": [
    { "name": "result", "valueBoolean": true },
    { "name": "display", "valueString": "Diabetes mellitus" }
  ]
}
```

---

## Appendix B: ECL Quick Reference

SNOMED CT Expression Constraint Language enables powerful queries:

| Query | ECL Expression |
|-------|---------------|
| Exact concept | `73211009` |
| Descendants of diabetes | `< 73211009` |
| Descendants including self | `<< 73211009` |
| Children only | `<! 73211009` |
| Ancestors | `> 73211009` |
| Procedures on heart | `< 71388002 : 363704007 = << 80891009` |
| Diabetes with body site | `< 73211009 : 363698007 = *` |

Use ECL in ValueSet URLs:
```
http://snomed.info/sct?fhir_vs=ecl/<< 73211009
```

---

## Change Log

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 0.1 | 2026-01-31 | Chregi | Initial draft |
