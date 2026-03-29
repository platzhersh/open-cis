# PRD: System Info View

## Overview

A new **System Info** page (`/system`) that gives users a quick overview of the running system: component health, registered openEHR templates, version information, and basic data statistics.

## Motivation

Open CIS is a learning/experimentation platform with multiple moving parts (FastAPI, EHRBase, two PostgreSQL databases). Today there is no single place to check whether everything is up, which templates are loaded, or what version is deployed. A System Info view closes that gap and aids debugging, onboarding, and demos.

## Requirements

### 1. System Architecture Diagram with Health Status

A simple visual diagram showing the system components and their real-time health:

| Component | Health Check Method | Shown Info |
|-----------|-------------------|------------|
| **Open CIS API** | `GET /health` | Status (healthy/degraded) |
| **App Database** (PostgreSQL) | Included in `/health` response (`database` field) | connected / disconnected |
| **EHRBase** | `ehrbase_client.health_check()` | available / unavailable |
| **EHRBase Database** | Implicit (EHRBase health implies its DB is up) | derived from EHRBase status |

**Visual design:**
- Block diagram showing: `Frontend → API → App DB` and `API → EHRBase → EHRBase DB`
- Each block shows a green/red/yellow status indicator
- Refreshable on demand (button) or auto-poll every 30 seconds

### 2. Registered openEHR Templates

A table listing all templates registered in EHRBase, fetched via `ehrbase_client.list_templates()`.

| Column | Source |
|--------|--------|
| Template ID | `template_id` from EHRBase response |
| Concept / Name | `concept` from EHRBase response |
| Archetype ID | `archetype_id` from EHRBase response |

- Empty state: message indicating no templates are registered, with a hint to upload templates
- Loading state: skeleton/spinner while fetching

### 3. Version Information

Display version details for key components:

| Item | Source |
|------|--------|
| **App Version** | `GET /api/version` (already exists) |
| **EHRBase Version** | Parse from EHRBase `/status` endpoint response |
| **Frontend Version** | `__APP_VERSION__` (already injected at build time) |

### 4. Data Statistics (counts)

Quick overview of data volume — useful for demos and sanity checks:

| Stat | Source |
|------|--------|
| Registered Patients | `SELECT COUNT(*) FROM PatientRegistry` |
| Encounters | `SELECT COUNT(*) FROM Encounter` |
| Audit Log Entries | `SELECT COUNT(*) FROM AuditLog` |

These are approximate counts for informational purposes, not real-time analytics.

## API Changes

### New Endpoint: `GET /api/system`

Returns all system info in a single response to minimize frontend round-trips. The endpoint always returns HTTP 200 — subsystem failures are represented in the response body, not via HTTP status codes.

#### Partial-Failure Envelope

Every top-level section follows a stable `{status, data, error}` shape so the frontend can deterministically handle nulls, partial responses, and per-item errors:

| Field | Type | Description |
|-------|------|-------------|
| `status` | `"ok"` \| `"partial"` \| `"error"` | Section-level rollup. `ok` = all data present, `partial` = some sub-items failed, `error` = entire section failed |
| `data` | `object` \| `array` \| `null` | Section payload. `null` only when `status` is `"error"` |
| `error` | `null` \| `{code: string, message: string}` | `null` when `status` is `"ok"`. Present when `status` is `"error"` or `"partial"` |

Sub-items within a section (e.g., individual components in `healthChecks`, individual counters in `dbCounts`) follow the same `{status, data, error}` shape, enabling per-item error display in the UI.

#### Full Response Schema

```json
{
  "healthChecks": {
    "status": "partial",
    "data": {
      "api": {
        "status": "ok",
        "data": { "status": "healthy" },
        "error": null
      },
      "database": {
        "status": "ok",
        "data": { "status": "connected" },
        "error": null
      },
      "ehrbase": {
        "status": "error",
        "data": null,
        "error": { "code": "EHRBASE_UNAVAILABLE", "message": "Cannot connect to EHRBase. Is it running?" }
      }
    },
    "error": { "code": "PARTIAL_HEALTH", "message": "One or more health checks failed" }
  },
  "version": {
    "status": "partial",
    "data": {
      "api": "0.5.0",
      "ehrbase": null
    },
    "error": { "code": "PARTIAL_VERSION", "message": "Could not determine EHRBase version" }
  },
  "templates": {
    "status": "ok",
    "data": [
      {
        "template_id": "IDCR - Vital Signs Encounter.v1",
        "concept": "Vital Signs Encounter",
        "archetype_id": "openEHR-EHR-COMPOSITION.encounter.v1"
      }
    ],
    "error": null
  },
  "dbCounts": {
    "status": "ok",
    "data": {
      "patients": 42,
      "encounters": 128,
      "audit_logs": 1024
    },
    "error": null
  }
}
```

#### Status Derivation Rules

| Section | `"ok"` | `"partial"` | `"error"` |
|---------|--------|-------------|-----------|
| `healthChecks` | All components reachable | Some components unreachable | Cannot perform any health check |
| `version` | All versions resolved | Some versions unknown (e.g., EHRBase down) | Cannot determine any version |
| `templates` | Template list fetched | N/A (atomic operation) | EHRBase unreachable |
| `dbCounts` | All counts fetched | Some counts failed | Database disconnected |

The endpoint aggregates health checks, template listing, version info, and DB counts. Individual subsystem failures (e.g., EHRBase down) are isolated per section — they never fail the entire response.

## Frontend Changes

### New Route: `/system`

- Add navigation link in the top nav bar (e.g., "System" or a gear/info icon)
- Page sections, top to bottom:
  1. **Health / Architecture Diagram** — visual block diagram with status indicators
  2. **Version Info** — simple key-value display
  3. **Data Statistics** — card or key-value display with counts
  4. **Templates Table** — sortable table of registered templates

### Component Breakdown

| Component | Purpose |
|-----------|---------|
| `SystemInfoPage.vue` | Page container, fetches `GET /api/system` |
| `SystemHealthDiagram.vue` | Visual component diagram with status dots |
| `TemplateList.vue` | Table of registered templates |

### UX Notes

- Must support light and dark mode (per project standard)
- Loading states for all sections
- Graceful degradation: if EHRBase is down, still show API health + DB stats
- Auto-refresh toggle (default off) with 30s interval
- Responsive layout for mobile

## Non-Goals

- Real-time metrics / monitoring dashboards (Prometheus/Grafana territory)
- Template upload from this view (future enhancement)
- User management or access control settings
- Log viewing

## Technical Notes

- Backend: new `api/src/system/` module with `router.py`, `service.py`, `schemas.py`
- The service layer should call health checks and template listing in parallel (`asyncio.gather`) to minimize response time
- EHRBase template list is already available via `ehrbase_client.list_templates()`
- EHRBase version can be parsed from `GET /ehrbase/rest/status`
- DB counts via Prisma: `prisma.patientregistry.count()`, etc.
