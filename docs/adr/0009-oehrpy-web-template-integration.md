# ADR-0009: oehrpy Web Template Integration for FLAT Path Sourcing

**Date:** 2026-04-04

## Status

Accepted — oehrpy v0.7.0 implements the Web Template client
(see oehrpy ADR-0003)

## Context

Open CIS uses oehrpy as its Python SDK for openEHR composition building and
submission to EHRBase. The current integration (oehrpy v0.1.0) centres on
`VitalSignsBuilder`, which constructs FLAT format compositions and submits them
to EHRBase via `EHRBaseClient`.

### How FLAT paths were established in v0.1.0

The FLAT path constants in `VitalSignsBuilder` were derived empirically during
integration testing. After repeated `"Could not consume Parts"` rejections from
EHRBase when paths were naively inferred from the OPT XML, the correct paths
were discovered by fetching the Web Template from EHRBase:

```
GET /rest/openehr/v1/definition/template/adl1.4/IDCR - Vital Signs Encounter.v1
Accept: application/openehr.wt+json
```

The `tree.id` values in that response were then hardcoded into the builder:

```python
_COMPOSITION_PREFIX = "vital_signs_observations"
_BP_PREFIX = "vital_signs_observations/vital_signs/blood_pressure"
_PULSE_PREFIX = "vital_signs_observations/vital_signs/pulse_heart_beat"
```

This works for the current single template, but it is a brittle approach:

- Paths are hardcoded strings with no runtime verification against the CDR
- Adding a second template (e.g., CH VACD vaccination, PRD-0005) requires
  repeating the same manual discovery process
- If the template is updated and re-uploaded, path changes are silently missed
  until EHRBase rejects a composition at runtime
- There is no infrastructure in the FastAPI layer to fetch, cache, or validate
  Web Templates

### The broader principle

oehrpy ADR-0003 ("Web Template as Primary Source of Truth for FLAT Paths")
formally establishes that FLAT paths must be sourced from the Web Template JSON,
not inferred from OPT XML. oehrpy v0.7.0 implements this by introducing a
`WebTemplateClient` on `EHRBaseClient` and in-memory Web Template caching.

Open CIS needs to adopt this pattern consistently so that the current accidental
correctness of `VitalSignsBuilder`'s hardcoded paths becomes explicit and
verifiable, and so that future templates (vaccination, SMART on FHIR) can be
added without repeating the manual discovery process.

## Decision

Open CIS will integrate oehrpy's Web Template support (available from v0.7.0)
as follows:

### 1. Upgrade oehrpy dependency to v0.7.0

`api/pyproject.toml` (or `requirements.txt`) pins `oehrpy>=0.2.0`. This is a
prerequisite for all points below.

### 2. Web Template fetch on API startup

The FastAPI lifespan handler (`api/src/main.py`) fetches and caches the Web
Template for each registered template at startup, alongside the existing OPT
upload step:

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    await ehrbase.upload_required_templates()
    await ehrbase.warm_web_template_cache(REQUIRED_TEMPLATES)
    yield
```

`warm_web_template_cache` calls `EHRBaseClient.get_web_template(template_id)`
for each template and holds the result in the client's in-memory cache. If
EHRBase is unreachable at startup the API continues (graceful degradation, same
policy as template upload), but logs a warning.

### 3. VitalSignsBuilder path constants remain, but are explicitly documented

The hardcoded path constants in `VitalSignsBuilder` are not removed in this
ADR's scope — they are known-correct values sourced from the Web Template and
confirmed working against EHRBase 2.26.0. They are annotated with a comment
that links to this ADR and documents how they were derived:

```python
# Paths sourced from Web Template: IDCR - Vital Signs Encounter.v1
# Retrieved 2026-01-09 from EHRBase 2.26.0 via
#   GET /rest/openehr/v1/definition/template/adl1.4/{id}
#   Accept: application/openehr.wt+json
# See Open CIS ADR-0009 and oehrpy ADR-0003.
_COMPOSITION_PREFIX = "vital_signs_observations"
```

### 4. New builders must derive paths from Web Template

Any composition builder added after this ADR — starting with
`ImmunizationBuilder` (PRD-0005, CH VACD template) — must derive its FLAT path
constants from the Web Template, not from OPT analysis. The process is:

1. Upload the OPT to EHRBase
2. Fetch the Web Template (`GET` with `Accept: application/openehr.wt+json`)
3. Navigate `tree.children` to extract `id` fields at each level
4. Hardcode the resulting path strings, annotated as above

The `/example?format=FLAT` endpoint is a useful cross-check: request a sample
composition and verify that your path strings match the keys returned.

### 5. path_mappings in API responses use Web Template-verified paths

`OpenEHRMetadata.path_mappings` returned by `GET /api/observations/vitals`
must show the correct EHRBase 2.26.0 FLAT paths, not the stale pre-discovery
format documented in PRD-0004. The `flat_path` values must match the
`_*_PREFIX` constants in `VitalSignsBuilder`:

```python
# Correct (post-ADR-0009)
PathMapping(
    field="systolic",
    flat_path="vital_signs_observations/vital_signs/blood_pressure/systolic",
)

# Stale (pre-ADR-0009, must be removed)
# PathMapping(
#     field="systolic",
#     flat_path="vital_signs/blood_pressure:0/any_event:0/systolic",
# )
```

### 6. No FlatValidator integration in this ADR's scope

oehrpy's `FlatValidator` (PRD-0002 in oehrpy, v0.7.0) is not integrated into
Open CIS's FastAPI layer in this ADR. Validation before submission to EHRBase
remains the responsibility of Pydantic models on the API boundary and EHRBase's
own composition validation. `FlatValidator` integration may be revisited in a
future ADR once it has stabilised in the oehrpy ecosystem.

## Alternatives Considered

### Keep hardcoded paths, no oehrpy v0.7.0 dependency

Continue using oehrpy v0.1.0 with the existing hardcoded path constants
indefinitely.

**Rejected.** This is the status quo that breaks silently on template updates and
does not scale to additional templates. It also leaves the stale `path_mappings`
in the API response unaddressed.

### Fetch Web Template at request time (no startup warm-up)

Fetch the Web Template lazily on the first composition request, relying on
oehrpy's in-memory cache for subsequent calls.

**Partially adopted.** oehrpy's cache handles this transparently after the first
fetch. The startup warm-up in point 2 above is added *in addition* to this,
to surface connectivity issues early (at boot time rather than at the first
patient request) and to guarantee zero-latency first requests.

### Generate builders dynamically from Web Template at runtime

Instead of hardcoded path constants, build the FLAT payload by traversing the
cached Web Template tree at runtime for every composition created.

**Deferred.** This is the architecturally cleanest long-term approach and aligns
with oehrpy's stated direction for `BuilderGenerator`. However, it requires a
stable Web Template traversal API in oehrpy that does not yet exist in v0.7.0.
It can be adopted in a future ADR once oehrpy provides a tree-walking builder
interface.

## Consequences

### Positive

- The correctness of FLAT paths in Open CIS becomes explicit and auditable
  rather than accidental.
- Adding new templates (CH VACD, others) follows a documented, repeatable
  process instead of ad-hoc trial-and-error against EHRBase.
- The `path_mappings` in API responses accurately reflect the paths EHRBase
  actually uses, making the openEHR transparency panel useful to developers
  reading the UI.
- Startup warm-up surfaces EHRBase connectivity issues earlier.

### Negative

- A hard dependency on oehrpy v0.7.0 means Open CIS cannot release new
  template support until oehrpy v0.7.0 is published on PyPI.
- The manual path-derivation process (fetch Web Template, read `tree.id`
  fields, hardcode) is still required for each new template. It is documented
  and repeatable, but not automated.

### Neutral

- `VitalSignsBuilder` path constants are unchanged. This ADR adds documentation
  and process, not a code rewrite.
- The existing OPT upload on startup is unaffected. OPT files remain the
  artefact uploaded to EHRBase; Web Templates are fetched *from* EHRBase after
  upload.

## Related

- `docs/adr/0001-use-openehr.md` — OPT upload on startup
- `docs/prd/0004-vital-signs-chart.md` — Vital signs feature, contains stale
  `path_mappings` that must be corrected
- PRD-0005 (CH VACD vaccination showcase) — First new template to follow this
  ADR's builder process
- oehrpy ADR-0003 — The upstream decision this ADR implements in Open CIS
- `docs/FLAT_FORMAT_VERSIONS.md` in oehrpy — Reference for FLAT path
  construction from Web Template `tree.id` fields
