# PRD-0012: FHIR Terminology Server Integration

**Version:** 1.1
**Date:** 2026-04-10
**Status:** Draft
**Owner:** Open CIS Project
**Priority:** P2 (Required for CH VACD / vaccination showcase)

---

## Executive Summary

Integrate a FHIR-compatible terminology server into Open CIS to enable human-readable display of coded clinical values stored in openEHR compositions. openEHR archetypes embed SNOMED CT, LOINC, and other coded terminologies as raw `CODE_PHRASE` values (code + terminology ID). Without a terminology server, these codes are opaque to end users and to the FHIR interoperability layer. This PRD specifies a lightweight, server-side terminology client backed initially by the public Swiss FHIR terminology server (`https://tx.fhir.ch/r4`), with an optional self-hosted path for future production use.

---

## Problem Statement

### The Core Gap

When openEHR compositions are stored in EHRBase, coded values appear as raw `CODE_PHRASE` structures:

```json
{
  "_type": "DV_CODED_TEXT",
  "value": "363787002",
  "defining_code": {
    "_type": "CODE_PHRASE",
    "terminology_id": { "value": "SNOMED-CT" },
    "code_string": "363787002"
  }
}
```

The `value` field should carry the human-readable display term (e.g., *"Observable entity"*), but this is not always populated, especially in compositions built programmatically via oehrpy's `ImmunizationBuilder` or created from the CH VACD vaccination template. Without resolved display terms:

1. The **Composition Viewer** in Open CIS shows raw SNOMED/LOINC codes to clinical users — unacceptable for real clinical workflows.
2. The **FHIR API layer** (`/api/fhir/...`, ADR-0004) must emit `Coding.display` on FHIR resources it produces. Without terminology resolution, it either omits `display` (non-conformant) or guesses (unsafe).
3. The **CH VACD vaccination showcase** (PRD-0005) references Swiss-specific value sets (e.g., `http://fhir.ch/ig/ch-vacd/ValueSet/ch-vacd-vaccines-vs`). Validating that a recorded vaccine code belongs to the correct value set requires a terminology server.
4. The **SMART on FHIR vaccination app** (PRD-0006) uses medblocks-ui components that can bind to FHIR ValueSet `$expand` responses to populate dropdown choices. Without a terminology server endpoint, these dropdowns cannot be populated dynamically.

### Affected Terminology Systems

| System | Identifier in openEHR | Example codes |
|---|---|---|
| SNOMED CT | `SNOMED-CT` | `363787002`, `840539006` (COVID-19 vaccine) |
| LOINC | `LOINC` | `59408-5` (SpO2), `8480-6` (systolic BP) |
| ATC (drugs) | `ATC` | `J07BX03` (COVID-19 vaccine) |
| Swiss CH VACD value sets | FHIR canonical URL | `http://fhir.ch/ig/ch-vacd/ValueSet/ch-vacd-vaccines-vs` |
| HL7 observation interpretation | `http://terminology.hl7.org/CodeSystem/v3-ObservationInterpretation` | `L` (low), `H` (high) |

---

## Goals

1. Provide a thin `TerminologyService` in FastAPI that proxies FHIR `$lookup` and `$validate-code` / `ValueSet/$expand` calls to a configured upstream FHIR terminology server.
2. Use `https://tx.fhir.ch/r4` as the **default upstream** — publicly available, no auth, covers SNOMED CT, LOINC, ATC, and Swiss national value sets (CH VACD, CH Core).
3. Expose resolved display terms in composition API responses without blocking on terminology calls (lazy / on-demand resolution per the established Open CIS UX principle).
4. Expose a `GET /api/fhir/terminology/...` pass-through surface for use by medblocks-ui ValueSet `$expand` requests from the Vue frontend (PRD-0006).
5. Design the configuration so that swapping the upstream to a self-hosted Snowstorm Lite instance (ADR-0003) requires only an environment variable change, with zero code changes.

---

## Non-Goals

- Self-hosting a terminology server is **out of scope** for this PRD. That is deferred to a future ADR/PRD once production usage justifies it.
- Providing a full FHIR terminology server proxy (all operations) is out of scope. Only `CodeSystem/$lookup`, `ValueSet/$validate-code`, and `ValueSet/$expand` are required.
- Caching terminology data to a persistent store (database) is out of scope for v1. In-memory TTL cache is sufficient.

---

## Where Terminology Resolution Helps in the Current Codebase

### 1. Composition Viewer — `GET /api/patients/{id}/compositions/{uid}`

**Location:** `api/src/compositions/router.py` → response model

**Problem:** The composition detail endpoint returns the raw openEHR JSON from EHRBase. `DV_CODED_TEXT` nodes carry a `defining_code.code_string` but `value` (the display term) may be missing or stale.

**Solution:** A post-processing step in the FastAPI response enriches `DV_CODED_TEXT` nodes whose `value` is empty or numeric-looking by calling `CodeSystem/$lookup` for each unique code. This is done asynchronously with `asyncio.gather` and is bounded by an in-memory TTL cache so repeated renders of the same composition are fast.

**Benefit:** Clinical users see *"COVID-19 vaccine"* instead of `840539006`.

---

### 2. Vital Signs Chart — Observation interpretation codes

**Location:** `api/src/observations/router.py`

**Problem:** The IDCR Vital Signs template includes `DV_CODED_TEXT` interpretation fields using `http://terminology.hl7.org/CodeSystem/v3-ObservationInterpretation` (e.g. `L`, `H`, `N`). These are stored as code-only in EHRBase compositions.

**Solution:** `$lookup` against the Swiss terminology server (which mirrors HL7 terminology code systems) resolves `L` → *"Low"*, `H` → *"High"*, etc. The resolved display is returned alongside the magnitude in the chart data payload.

---

### 3. CH VACD Vaccination Showcase — `POST /api/patients/{id}/vaccinations` (PRD-0005)

**Location:** `api/src/vaccinations/router.py` (to be created per PRD-0005)

**Problem:** Vaccine codes submitted by the user (ATC codes like `J07BX03`, or SNOMED vaccine product codes) need to be validated as members of the CH VACD vaccine value set before being written to EHRBase. Without a terminology server, this validation is absent or requires maintaining a local static list.

**Solution:** Call `ValueSet/$validate-code` on `http://fhir.ch/ig/ch-vacd/ValueSet/ch-vacd-vaccines-vs` at the Swiss terminology server. Reject compositions that contain out-of-set codes with a `422 Unprocessable Entity` response and a descriptive error.

**Benefit:** Data quality gate enforced at the API layer, consistent with the CH VACD IG profile requirements.

---

### 4. FHIR API Layer — `/api/fhir/Immunization` (PRD-0006)

**Location:** `api/src/fhir/immunization.py` (to be created per PRD-0006)

**Problem:** When openFHIR translates an openEHR vaccination composition to a FHIR `Immunization` resource, the `vaccineCode.coding[].display` field must be populated for conformance to the CH VACD FHIR IG. openFHIR produces the mapping but does not call a terminology server to fill `display`.

**Solution:** A post-processing enrichment step in the FHIR router calls `CodeSystem/$lookup` for each `coding` element that is missing `display` before returning the FHIR resource to the caller.

---

### 5. medblocks-ui Dropdowns — `GET /api/fhir/ValueSet/$expand` (PRD-0006)

**Location:** `api/src/fhir/terminology.py` (new, this PRD)

**Problem:** medblocks-ui Web Components (e.g., `<mb-select>`) accept a FHIR `ValueSet/$expand` URL to populate their option lists. The component must call a FHIR-compatible endpoint. Open CIS's own domain is the appropriate origin to avoid CORS issues and to allow transparent upstream switching.

**Solution:** Expose `GET /api/fhir/ValueSet/{id}/$expand` (and `GET /api/fhir/CodeSystem/{id}/$lookup`) as thin, authenticated pass-throughs to the configured upstream. The Vue frontend configures medblocks-ui components with `terminologyUrl: "/api/fhir"`.

---

## Architecture

### Components

```
Vue 3 frontend
    │
    │  GET /api/patients/{id}/compositions/{uid}  (enriched)
    │  GET /api/fhir/ValueSet/{id}/$expand        (pass-through)
    ▼
FastAPI (Open CIS API)
    ├── TerminologyService  ←─── TerminologyClient (httpx, async)
    │       ├── lookup(system, code) → display_term
    │       ├── validate_code(value_set_url, system, code) → bool
    │       └── expand(value_set_url, filter?) → ValueSet
    │                │
    │                └──► https://tx.fhir.ch/r4   (default upstream)
    │                      (swap to Snowstorm Lite via env var)
    │
    ├── CompositionRouter   — enriches DV_CODED_TEXT display terms
    ├── VaccinationRouter   — calls validate_code before EHRBase write
    └── FhirRouter          — pass-through + enriches Immunization.display
```

### Configuration

```python
# api/src/config.py (additions)
TERMINOLOGY_SERVER_URL: str = "https://tx.fhir.ch/r4"
TERMINOLOGY_CACHE_TTL_SECONDS: int = 3600
TERMINOLOGY_ENABLED: bool = True
```

Switching to self-hosted Snowstorm Lite:

```bash
TERMINOLOGY_SERVER_URL=http://snowstorm:8080/fhir
```

No code changes required.

### TerminologyClient

```python
# api/src/terminology/client.py

class TerminologyClient:
    """Async FHIR R4 terminology client backed by httpx."""

    async def lookup(
        self,
        system: str,           # e.g. "http://snomed.info/sct"
        code: str,
    ) -> str | None:
        """Return display term for a code, or None if not found."""

    async def validate_code(
        self,
        value_set_url: str,    # canonical FHIR ValueSet URL
        system: str,
        code: str,
    ) -> bool:
        """Return True if code is a member of the given ValueSet."""

    async def expand(
        self,
        value_set_url: str,
        filter: str | None = None,
        count: int = 200,
    ) -> dict:
        """Return FHIR ValueSet $expand response as dict."""
```

### System identifier normalisation

openEHR compositions use short identifiers (`SNOMED-CT`, `LOINC`). FHIR uses canonical URIs. A translation table is required:

| openEHR `terminology_id` | FHIR `system` URI |
|---|---|
| `SNOMED-CT` | `http://snomed.info/sct` |
| `LOINC` | `http://loinc.org` |
| `ATC` | `http://www.whocc.no/atc` |
| `ICD10` | `http://hl7.org/fhir/sid/icd-10` |
| `openehr` | *(internal, skip)* |
| `local` | *(internal, skip)* |

This mapping lives in `api/src/terminology/systems.py` as a simple `dict[str, str]`.

### In-memory cache

Use `cachetools.TTLCache` keyed on `(system_uri, code)` for `$lookup` results and `(value_set_url, system_uri, code)` for `$validate-code` results. Default TTL: 1 hour. No Redis dependency for v1.

```python
from cachetools import TTLCache
_lookup_cache: TTLCache[tuple[str, str], str | None] = TTLCache(
    maxsize=10_000, ttl=TERMINOLOGY_CACHE_TTL_SECONDS
)
```

### Lazy enrichment pattern

Composition enrichment happens **after** the composition is fetched from EHRBase, in the API response handler — not in the CDR write path. This is consistent with the lazy resolution principle established across the project. The enrichment step:

1. Walks the composition JSON tree for `DV_CODED_TEXT` nodes where `defining_code.terminology_id.value` is not `local` or `openehr` and `value` is absent or matches a raw code pattern.
2. Collects unique `(system, code)` pairs.
3. Fires `asyncio.gather(*[client.lookup(s, c) for s, c in unique_pairs])` — a single concurrent batch.
4. Patches the `value` fields in the composition copy returned to the client. The raw composition stored in EHRBase is never modified.

---

## System Page Integration

The Open CIS system/status page must display the terminology server as a first-class infrastructure component alongside EHRBase and other services.

### Display Requirements

The terminology server card on the system page shows:

- **URL** — the configured `TERMINOLOGY_SERVER_URL` value
- **Status** — live connectivity indicator, resolved by calling `GET /api/terminology/health` on page load. States: `online` (green), `degraded` (yellow, reachable but slow > 2s), `offline` (red, timeout or 5xx)
- **Upstream type** — derived from the URL: `Swiss FHIR Terminology Server (tx.fhir.ch)` for the default, `Snowstorm Lite (self-hosted)` if the URL matches a local host, or the raw hostname for any other value
- **Relations to other components** — a brief list of which Open CIS features depend on it:
  - Composition Viewer — display term enrichment
  - Vital Signs — observation interpretation labels
  - Vaccinations — CH VACD value set validation (shown only if PRD-0005 feature is active)
  - FHIR API — `Coding.display` enrichment and ValueSet `$expand` pass-through (shown only if FHIR API feature is active)

### Backend

The existing `GET /api/terminology/health` endpoint (defined in the API Surface section above) is the sole backend requirement. It returns:

```json
{
  "status": "online" | "degraded" | "offline",
  "url": "https://tx.fhir.ch/r4",
  "response_ms": 312
}
```

The frontend polls this endpoint once on system page mount; no WebSocket or background polling is required.

---

## API Surface

### New endpoints (this PRD)

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/fhir/ValueSet/{id}/$expand` | Pass-through ValueSet expand to upstream |
| `GET` | `/api/fhir/ValueSet/$expand?url={url}` | Pass-through ValueSet expand by canonical URL |
| `GET` | `/api/fhir/CodeSystem/$lookup?system={s}&code={c}` | Pass-through code lookup |
| `GET` | `/api/terminology/health` | Connectivity check against upstream |

### Modified endpoints

| Method | Path | Change |
|---|---|---|
| `GET` | `/api/patients/{id}/compositions/{uid}` | `DV_CODED_TEXT.value` enriched on response |
| `GET` | `/api/patients/{id}/vitals` | Interpretation codes resolved to display terms |

---

## Implementation Plan

### Phase 1 — Core Client & Health Check (1–2 days)

- Add `httpx` async client dependency.
- Implement `TerminologyClient` with `lookup`, `validate_code`, `expand`.
- Implement `systems.py` normalisation table.
- Add `TTLCache` wrapper.
- Add `GET /api/terminology/health` endpoint.
- Add `TERMINOLOGY_SERVER_URL` env var to `docker-compose.yml` and `.env.example`.
- Write unit tests with `httpx.MockTransport`.

### Phase 2 — Composition Enrichment (1 day)

- Implement `enrich_composition(composition_json, client)` utility in `api/src/terminology/enrichment.py`.
- Wire into `GET /api/patients/{id}/compositions/{uid}` response handler.
- Integration test: store a composition with a SNOMED code, retrieve it, assert `value` is populated.

### Phase 3 — Vaccination Validation (tied to PRD-0005)

- Add `validate_code` call in vaccination write path before EHRBase POST.
- Return `422` with FHIR `OperationOutcome`-style error body on invalid code.
- Wire CH VACD value set URL from config (not hard-coded).

### Phase 4 — FHIR Pass-Through for medblocks-ui (tied to PRD-0006)

- Implement `GET /api/fhir/ValueSet/{id}/$expand` and `GET /api/fhir/CodeSystem/$lookup` pass-throughs.
- Add CORS header handling (pass-through must forward correct content-type).
- Document medblocks-ui configuration in Open CIS frontend (`terminologyUrl: "/api/fhir"`).

---

## Configuration Reference

| Variable | Default | Description |
|---|---|---|
| `TERMINOLOGY_SERVER_URL` | `https://tx.fhir.ch/r4` | Base URL of the FHIR R4 terminology server |
| `TERMINOLOGY_ENABLED` | `true` | Feature flag — set `false` to disable all terminology calls |
| `TERMINOLOGY_CACHE_TTL_SECONDS` | `3600` | TTL for in-memory lookup/validate cache |
| `TERMINOLOGY_TIMEOUT_SECONDS` | `5` | HTTP timeout for upstream calls; failures are soft (log + skip) |

**Failure mode:** If the terminology server is unreachable (timeout, 5xx), enrichment is skipped silently and the raw `code_string` is returned. The system must not fail a composition read because of a terminology server outage.

---

## Future Path to Self-Hosted Snowstorm Lite

Per ADR-0003, Snowstorm Lite is the selected self-hosted option when Open CIS moves beyond the public server. The migration path is:

1. Add `snowstorm-lite` container to `docker-compose.yml`.
2. Load required SNOMED CT snapshot and CH extension into Snowstorm Lite at startup.
3. Set `TERMINOLOGY_SERVER_URL=http://snowstorm-lite:8080/fhir` in the production `.env`.
4. No application code changes required.

Note: Snowstorm Lite does not cover LOINC or ATC by default. A mixed upstream strategy (route by `system` URI) may be needed if full terminology coverage is required in production.

---

## Success Criteria

- `GET /api/patients/{id}/compositions/{uid}` returns `DV_CODED_TEXT.value` populated with human-readable display terms for SNOMED CT codes present in vital signs compositions.
- A POST to the vaccination endpoint with a code outside the CH VACD vaccine value set returns `422`.
- `GET /api/fhir/ValueSet/{id}/$expand` returns a valid FHIR ValueSet and can be consumed by a medblocks-ui `<mb-select>` component.
- `GET /api/terminology/health` returns `200` when `tx.fhir.ch` is reachable.
- Changing `TERMINOLOGY_SERVER_URL` to a local Snowstorm Lite instance requires no code changes.
- The system page displays the terminology server card with URL, live status, and the list of dependent features.
- Terminology server downtime does not degrade composition read availability (soft failure).

---

## Related Documents

- [ADR-0003: Snowstorm Lite as Self-Hosted Terminology Server](../adr/ADR-0003-snowstorm-lite-terminology.md)
- [ADR-0004: Two-Level API Surface (`/api` and `/api/fhir`)](../adr/ADR-0004-two-level-api-surface.md)
- [PRD-0005: CH VACD Vaccination Showcase](PRD-0005-ch-vacd-vaccination.md)
- [PRD-0006: SMART on FHIR Vaccination App](PRD-0006-smart-on-fhir.md)
- Swiss FHIR Terminology Server: `https://tx.fhir.ch/r4`
- Snowstorm Lite: `https://github.com/IHTSDO/snowstorm-lite`

---

## Change Log

| Version | Date | Author | Changes |
|---|---|---|---|
| 1.0 | 2026-04-10 | Open CIS Team | Initial draft |
| 1.1 | 2026-04-10 | Open CIS Team | Removed oehrpy and openEHR Explorer references; scope strictly Open CIS |
