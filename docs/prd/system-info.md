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

### New Endpoint: `GET /api/system/info`

Returns all system info in a single response to minimize frontend round-trips:

```json
{
  "versions": {
    "api": "0.5.0",
    "ehrbase": "2.0.0"
  },
  "health": {
    "api": "healthy",
    "database": "connected",
    "ehrbase": "available"
  },
  "templates": [
    {
      "template_id": "vital_signs_v2",
      "concept": "Vital Signs",
      "archetype_id": "openEHR-EHR-COMPOSITION.encounter.v1"
    }
  ],
  "stats": {
    "patients": 42,
    "encounters": 128,
    "audit_logs": 1024
  }
}
```

The endpoint aggregates health checks, template listing, version info, and DB counts. Individual failures (e.g., EHRBase down) should not fail the entire response — return partial data with null/error markers for unavailable sections.

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
| `SystemInfoPage.vue` | Page container, fetches `/api/system/info` |
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
