# PRD-0004: Vital Signs Chart with openEHR Transparency

**Version:** 1.0
**Date:** 2026-01-03
**Status:** Draft
**Owner:** Open CIS Project

---

## Executive Summary

Implement vital signs recording and visualization with a time-series chart, supporting blood pressure and pulse rate as initial observations. A key differentiator of this feature is **openEHR transparency**: users can inspect how clinical data maps to openEHR archetypes, templates, and paths, making the underlying data model visible for educational purposes.

This feature bridges the gap between the user-friendly clinical interface and the openEHR foundation, helping users understand how standardized clinical data modeling works.

---

## Problem Statement

**Current State:**
- The observations module exists as a placeholder (`api/src/observations/`)
- AQL queries for blood pressure are defined but compositions are not created
- No templates (OPT files) are deployed to EHRBase
- No way to visualize vital signs over time
- Users cannot see how data maps to openEHR structures

**User Personas:**
1. **Clinical Staff** - Needs to record and view patient vital signs during encounters
2. **Developers/Learners** - Wants to understand how data is stored in openEHR
3. **Integration Engineers** - Needs to see archetype paths for AQL queries and integrations

---

## Goals & Success Metrics

### Goals
- Record vital signs (blood pressure, pulse) and store in EHRBase as compositions
- Display vital signs history as an interactive time-series chart
- Expose openEHR metadata (archetypes, paths, composition structure) in the UI
- Provide educational value by showing the openEHR data model

### Success Metrics
- Vital signs can be recorded and retrieved via UI
- Chart displays last 30 days of readings with zoom/pan
- openEHR metadata panel accessible for any observation
- < 2 second load time for vital signs chart (up to 100 readings)

---

## openEHR Architecture

### Archetypes Used

This feature uses well-established openEHR Clinical Knowledge Manager (CKM) archetypes:

| Archetype ID | Description | CKM Link |
|--------------|-------------|----------|
| `openEHR-EHR-OBSERVATION.blood_pressure.v2` | Blood pressure measurement | [CKM](https://ckm.openehr.org/ckm/archetypes/1013.1.3574) |
| `openEHR-EHR-OBSERVATION.pulse.v2` | Pulse/heart rate measurement | [CKM](https://ckm.openehr.org/ckm/archetypes/1013.1.170) |
| `openEHR-EHR-COMPOSITION.encounter.v1` | Container for encounter-based observations | [CKM](https://ckm.openehr.org/ckm/archetypes/1013.1.1366) |

### Template Definition

We will create an Operational Template (OPT) that combines these archetypes:

**Template ID:** `open-cis.vital-signs.v1`

**Structure:**
```
COMPOSITION (openEHR-EHR-COMPOSITION.encounter.v1)
├── context
│   ├── start_time
│   └── setting (ambulatory, emergency, etc.)
├── OBSERVATION (openEHR-EHR-OBSERVATION.blood_pressure.v2)
│   └── data
│       └── events[at0006] (any event)
│           ├── time
│           └── data
│               ├── items[at0004] (systolic) - magnitude, units
│               └── items[at0005] (diastolic) - magnitude, units
└── OBSERVATION (openEHR-EHR-OBSERVATION.pulse.v2)
    └── data
        └── events[at0003] (any event)
            ├── time
            └── data
                └── items[at0004] (rate) - magnitude, units
```

### FLAT Format Example

When creating a composition, the FLAT format maps UI fields to openEHR paths:

```json
{
  "ctx/language": "en",
  "ctx/territory": "US",
  "ctx/time": "2026-01-03T10:30:00Z",
  "open-cis.vital-signs.v1/context/start_time": "2026-01-03T10:30:00Z",
  "open-cis.vital-signs.v1/blood_pressure/any_event/systolic|magnitude": 120,
  "open-cis.vital-signs.v1/blood_pressure/any_event/systolic|unit": "mm[Hg]",
  "open-cis.vital-signs.v1/blood_pressure/any_event/diastolic|magnitude": 80,
  "open-cis.vital-signs.v1/blood_pressure/any_event/diastolic|unit": "mm[Hg]",
  "open-cis.vital-signs.v1/blood_pressure/any_event/time": "2026-01-03T10:30:00Z",
  "open-cis.vital-signs.v1/pulse/any_event/rate|magnitude": 72,
  "open-cis.vital-signs.v1/pulse/any_event/rate|unit": "/min",
  "open-cis.vital-signs.v1/pulse/any_event/time": "2026-01-03T10:30:00Z"
}
```

---

## Data Model

### VitalSigns (Application View)

This is the simplified view used in the API and frontend:

```typescript
// web/src/types/vitals.ts

export interface VitalSignsReading {
  id: string                    // composition_uid from EHRBase
  patient_id: string
  encounter_id?: string         // optional link to encounter
  recorded_at: string           // ISO 8601 timestamp

  // Blood pressure
  systolic?: number             // mm[Hg]
  diastolic?: number            // mm[Hg]

  // Pulse
  pulse_rate?: number           // /min (beats per minute)

  // Metadata
  created_at: string

  // openEHR transparency
  openehr_metadata: OpenEHRMetadata
}

export interface OpenEHRMetadata {
  composition_uid: string
  template_id: string
  archetype_ids: string[]
  ehr_id: string

  // Path mappings for transparency
  path_mappings: PathMapping[]
}

export interface PathMapping {
  field: string                 // UI field name (e.g., "systolic")
  archetype_id: string          // e.g., "openEHR-EHR-OBSERVATION.blood_pressure.v2"
  archetype_path: string        // e.g., "/data[at0001]/events[at0006]/data[at0003]/items[at0004]/value"
  flat_path: string             // e.g., "open-cis.vital-signs.v1/blood_pressure/any_event/systolic"
  value: any                    // actual value
  unit?: string                 // unit if applicable
}
```

### Python Schemas

```python
# api/src/observations/schemas.py

from datetime import datetime
from pydantic import BaseModel, Field


class VitalSignsCreate(BaseModel):
    patient_id: str
    encounter_id: str | None = None
    recorded_at: datetime

    # Blood pressure (optional - can record just pulse)
    systolic: int | None = Field(None, ge=50, le=300)
    diastolic: int | None = Field(None, ge=30, le=200)

    # Pulse (optional - can record just BP)
    pulse_rate: int | None = Field(None, ge=20, le=300)

    @model_validator(mode='after')
    def at_least_one_vital(self) -> 'VitalSignsCreate':
        if self.systolic is None and self.diastolic is None and self.pulse_rate is None:
            raise ValueError('At least one vital sign must be provided')
        if (self.systolic is None) != (self.diastolic is None):
            raise ValueError('Both systolic and diastolic must be provided together')
        return self


class PathMappingResponse(BaseModel):
    field: str
    archetype_id: str
    archetype_path: str
    flat_path: str
    value: float | int | str | None
    unit: str | None = None


class OpenEHRMetadataResponse(BaseModel):
    composition_uid: str
    template_id: str
    archetype_ids: list[str]
    ehr_id: str
    path_mappings: list[PathMappingResponse]


class VitalSignsResponse(BaseModel):
    id: str
    patient_id: str
    encounter_id: str | None
    recorded_at: datetime
    systolic: int | None
    diastolic: int | None
    pulse_rate: int | None
    created_at: datetime
    openehr_metadata: OpenEHRMetadataResponse


class VitalSignsListResponse(BaseModel):
    items: list[VitalSignsResponse]
    total: int
```

---

## API Endpoints

### Vital Signs CRUD

```
POST   /api/observations/vital-signs              # Record vital signs
GET    /api/observations/vital-signs              # List all (with filters)
GET    /api/observations/vital-signs/{id}         # Get by composition UID
DELETE /api/observations/vital-signs/{id}         # Delete composition

GET    /api/patients/{patient_id}/vital-signs     # Patient's vital signs
GET    /api/encounters/{encounter_id}/vital-signs # Encounter's vital signs
```

### openEHR Metadata Endpoints

```
GET    /api/openehr/templates                     # List available templates
GET    /api/openehr/templates/{id}                # Get template details
GET    /api/openehr/templates/{id}/example        # Get example composition
GET    /api/openehr/archetypes/{id}               # Get archetype info (proxied from CKM)
GET    /api/openehr/compositions/{uid}            # Get raw composition (FLAT or STRUCTURED)
GET    /api/openehr/compositions/{uid}/paths      # Get all paths in composition
```

### Query Parameters

**GET /api/observations/vital-signs:**
- `patient_id`: Filter by patient (required unless admin)
- `encounter_id`: Filter by encounter
- `from_date`: Start of date range
- `to_date`: End of date range
- `skip`: Pagination offset (default: 0)
- `limit`: Page size (default: 100, max: 1000)

### Request/Response Examples

**Record Vital Signs:**
```http
POST /api/observations/vital-signs
Content-Type: application/json

{
  "patient_id": "cm123456789",
  "encounter_id": "enc_abc123",
  "recorded_at": "2026-01-03T10:30:00Z",
  "systolic": 120,
  "diastolic": 80,
  "pulse_rate": 72
}

Response: 201 Created
{
  "id": "f47ac10b-58cc-4372-a567-0e02b2c3d479::open-cis::1",
  "patient_id": "cm123456789",
  "encounter_id": "enc_abc123",
  "recorded_at": "2026-01-03T10:30:00Z",
  "systolic": 120,
  "diastolic": 80,
  "pulse_rate": 72,
  "created_at": "2026-01-03T10:30:05Z",
  "openehr_metadata": {
    "composition_uid": "f47ac10b-58cc-4372-a567-0e02b2c3d479::open-cis::1",
    "template_id": "open-cis.vital-signs.v1",
    "archetype_ids": [
      "openEHR-EHR-COMPOSITION.encounter.v1",
      "openEHR-EHR-OBSERVATION.blood_pressure.v2",
      "openEHR-EHR-OBSERVATION.pulse.v2"
    ],
    "ehr_id": "7d44b88c-4199-4bad-97dc-d78268e01398",
    "path_mappings": [
      {
        "field": "systolic",
        "archetype_id": "openEHR-EHR-OBSERVATION.blood_pressure.v2",
        "archetype_path": "/data[at0001]/events[at0006]/data[at0003]/items[at0004]/value/magnitude",
        "flat_path": "open-cis.vital-signs.v1/blood_pressure/any_event/systolic|magnitude",
        "value": 120,
        "unit": "mm[Hg]"
      },
      {
        "field": "diastolic",
        "archetype_id": "openEHR-EHR-OBSERVATION.blood_pressure.v2",
        "archetype_path": "/data[at0001]/events[at0006]/data[at0003]/items[at0005]/value/magnitude",
        "flat_path": "open-cis.vital-signs.v1/blood_pressure/any_event/diastolic|magnitude",
        "value": 80,
        "unit": "mm[Hg]"
      },
      {
        "field": "pulse_rate",
        "archetype_id": "openEHR-EHR-OBSERVATION.pulse.v2",
        "archetype_path": "/data[at0002]/events[at0003]/data[at0001]/items[at0004]/value/magnitude",
        "flat_path": "open-cis.vital-signs.v1/pulse/any_event/rate|magnitude",
        "value": 72,
        "unit": "/min"
      }
    ]
  }
}
```

**Get Raw Composition (for transparency):**
```http
GET /api/openehr/compositions/f47ac10b-58cc-4372-a567-0e02b2c3d479::open-cis::1?format=flat

Response: 200 OK
{
  "format": "FLAT",
  "template_id": "open-cis.vital-signs.v1",
  "composition": {
    "ctx/language": "en",
    "ctx/territory": "US",
    "open-cis.vital-signs.v1/context/start_time": "2026-01-03T10:30:00Z",
    "open-cis.vital-signs.v1/blood_pressure/any_event/systolic|magnitude": 120,
    "open-cis.vital-signs.v1/blood_pressure/any_event/systolic|unit": "mm[Hg]",
    ...
  }
}
```

---

## User Interface Design

### Vital Signs Chart (Patient Detail Page)

Add a new "Vital Signs" tab or section to PatientDetailPage:

```
┌─────────────────────────────────────────────────────────────────┐
│ John Doe (MRN-12345)                                            │
├─────────────────────────────────────────────────────────────────┤
│ [Overview] [Vital Signs] [Encounters] [Documents]               │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Vital Signs                               [+ Record Vitals]    │
│                                                                 │
│  Date Range: [Last 30 days ▼]  Metrics: [All ▼]                │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  Blood Pressure (mmHg)                                   │   │
│  │  160 ─┬──────────────────────────────────────────────   │   │
│  │  140 ─┤     ●                                            │   │
│  │  120 ─┤  ●     ●  ●     ●  ●  ●  ●  ●                   │   │ ← Systolic
│  │  100 ─┤                                                  │   │
│  │   80 ─┤  ●  ●  ●  ●  ●  ●  ●  ●  ●  ●                   │   │ ← Diastolic
│  │   60 ─┴──────────────────────────────────────────────   │   │
│  │       Jan 1  Jan 5  Jan 10  Jan 15  Jan 20              │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  Pulse Rate (bpm)                                        │   │
│  │  100 ─┬──────────────────────────────────────────────   │   │
│  │   80 ─┤        ●                                         │   │
│  │   72 ─┤  ●  ●     ●  ●  ●  ●  ●  ●  ●                   │   │
│  │   60 ─┤                                                  │   │
│  │   40 ─┴──────────────────────────────────────────────   │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  Recent Readings                                                │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ Date/Time          │ BP        │ Pulse │ Actions         │  │
│  │─────────────────────────────────────────────────────────│  │
│  │ Jan 3, 10:30 AM    │ 120/80    │ 72    │ [ℹ️ openEHR]    │  │
│  │ Jan 2, 2:15 PM     │ 118/78    │ 68    │ [ℹ️ openEHR]    │  │
│  │ Jan 1, 9:00 AM     │ 142/92    │ 88    │ [ℹ️ openEHR]    │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Record Vital Signs Dialog

```
┌─────────────────────────────────────────────────────────────┐
│ Record Vital Signs                                      [×] │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Patient: John Doe (MRN-12345)                              │
│                                                             │
│  Date & Time *                                              │
│  [01/03/2026] [10:30 AM]  [Now]                            │
│                                                             │
│  Encounter (optional)                                       │
│  [Select encounter...                            ▼]         │
│                                                             │
│  ─────────────────────────────────────────────────────────  │
│  Blood Pressure                                             │
│                                                             │
│  Systolic *          Diastolic *                            │
│  [120    ] mmHg      [80     ] mmHg                        │
│                                                             │
│  ─────────────────────────────────────────────────────────  │
│  Pulse                                                      │
│                                                             │
│  Heart Rate                                                 │
│  [72     ] bpm                                              │
│                                                             │
│  ─────────────────────────────────────────────────────────  │
│                                                             │
│  [Show openEHR Preview ▼]                                   │
│                                                             │
│                              [Cancel] [Record Vital Signs]  │
└─────────────────────────────────────────────────────────────┘
```

### openEHR Metadata Panel

When user clicks "openEHR" button on a reading, show a slide-over panel:

```
┌─────────────────────────────────────────────────────────────┐
│ openEHR Data Structure                                  [×] │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Composition                                                │
│  UID: f47ac10b-58cc-4372-a567-0e02b2c3d479::open-cis::1    │
│  Template: open-cis.vital-signs.v1                          │
│  EHR ID: 7d44b88c-4199-4bad-97dc-d78268e01398              │
│                                                             │
│  ─────────────────────────────────────────────────────────  │
│                                                             │
│  Archetypes Used                                            │
│                                                             │
│  📦 openEHR-EHR-COMPOSITION.encounter.v1                   │
│     Container for clinical encounter                        │
│     [View in CKM ↗]                                        │
│                                                             │
│  📦 openEHR-EHR-OBSERVATION.blood_pressure.v2              │
│     Blood pressure measurement                              │
│     [View in CKM ↗]                                        │
│                                                             │
│  📦 openEHR-EHR-OBSERVATION.pulse.v2                       │
│     Pulse/heart rate measurement                            │
│     [View in CKM ↗]                                        │
│                                                             │
│  ─────────────────────────────────────────────────────────  │
│                                                             │
│  Data Path Mappings                                         │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Systolic: 120 mmHg                                   │   │
│  │                                                      │   │
│  │ Archetype Path:                                      │   │
│  │ /data[at0001]/events[at0006]/data[at0003]/          │   │
│  │   items[at0004]/value/magnitude                      │   │
│  │                                                      │   │
│  │ FLAT Path:                                           │   │
│  │ open-cis.vital-signs.v1/blood_pressure/              │   │
│  │   any_event/systolic|magnitude                       │   │
│  │                                                [Copy]│   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Diastolic: 80 mmHg                                   │   │
│  │ ...                                                  │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ─────────────────────────────────────────────────────────  │
│                                                             │
│  Raw Composition Data                                       │
│  Format: [FLAT ▼] [STRUCTURED] [CANONICAL JSON]            │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ {                                                    │   │
│  │   "ctx/language": "en",                              │   │
│  │   "ctx/territory": "US",                             │   │
│  │   "open-cis.vital-signs.v1/context/start_time":     │   │
│  │     "2026-01-03T10:30:00Z",                          │   │
│  │   "open-cis.vital-signs.v1/blood_pressure/          │   │
│  │     any_event/systolic|magnitude": 120,              │   │
│  │   ...                                                │   │
│  │ }                                              [Copy]│   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  [View AQL Query Example]                                   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Global openEHR Info Access

Add openEHR info button to other resources:

**Patient Detail Page:**
```
System Information
├── Patient ID: cm123456789
├── MRN: MRN-12345
├── EHR ID: 7d44b88c-4199-4bad-97dc-d78268e01398  [ℹ️ openEHR]
└── Created: Jan 1, 2026
```

**Encounter Detail Page:**
```
Encounter enc_abc123
├── Type: Ambulatory
├── Status: Finished
└── Linked Compositions: 3  [ℹ️ View in openEHR]
```

---

## Chart Implementation

### Technology Choice

Use **Chart.js** with vue-chartjs wrapper for the vital signs chart:
- Lightweight and well-documented
- Good time-series support
- Responsive and touch-friendly
- Already commonly used with Vue

### Chart Features

1. **Dual Y-axis**: Blood pressure on left, pulse on right
2. **Tooltips**: Show exact values and timestamp on hover
3. **Click to inspect**: Click data point to show openEHR metadata
4. **Zoom/Pan**: Mouse wheel zoom, drag to pan
5. **Date range selector**: Presets (7d, 30d, 90d, 1y) + custom range
6. **Reference lines**: Show normal ranges (systolic 90-120, diastolic 60-80, pulse 60-100)
7. **Anomaly highlighting**: Color-code readings outside normal range

### Normal Ranges (WHO Guidelines)

| Vital Sign | Normal | Elevated | High |
|------------|--------|----------|------|
| Systolic | < 120 | 120-139 | ≥ 140 |
| Diastolic | < 80 | 80-89 | ≥ 90 |
| Pulse | 60-100 | - | < 60 or > 100 |

---

## Implementation Plan

### Phase 1: Backend Foundation

**Template & EHRBase Setup:**
- [ ] Create OPT file for vital signs template
- [ ] Add template upload script/migration
- [ ] Verify template deployment to EHRBase

**API Implementation:**
- [ ] Update `observations/schemas.py` with new models
- [ ] Implement `observations/service.py` composition creation
- [ ] Add CRUD endpoints in `observations/router.py`
- [ ] Implement openEHR metadata extraction
- [ ] Add `/api/openehr/` endpoints for transparency

**Testing:**
- [ ] Unit tests for vital signs service
- [ ] Integration tests with EHRBase
- [ ] Test AQL queries for retrieval

### Phase 2: Frontend - Core Features

**Components:**
- [ ] Create `VitalSignsChart.vue` component
- [ ] Create `RecordVitalsDialog.vue` component
- [ ] Create `VitalSignsTable.vue` component
- [ ] Add vitals store (Pinia)

**Integration:**
- [ ] Add Vital Signs tab to PatientDetailPage
- [ ] Wire up API calls
- [ ] Implement chart with Chart.js

### Phase 3: openEHR Transparency

**Metadata Panel:**
- [ ] Create `OpenEHRMetadataPanel.vue` component
- [ ] Implement path mapping display
- [ ] Add raw composition viewer (FLAT/STRUCTURED)
- [ ] Add CKM links for archetypes

**Extended Integration:**
- [ ] Add openEHR info to Patient detail (EHR ID)
- [ ] Add openEHR info to Encounter detail
- [ ] Add AQL query examples

### Phase 4: Polish

- [ ] Add reference lines to chart
- [ ] Implement anomaly highlighting
- [ ] Add zoom/pan functionality
- [ ] Loading states and error handling
- [ ] Write E2E tests

---

## Template Files

### OPT File Location

Create template file at: `api/templates/open-cis.vital-signs.v1.opt`

The OPT file will be generated using:
1. Archetype Designer (web-based)
2. Or ADL Designer
3. Export as Operational Template XML

### Template Upload

Add to startup or migration:

```python
# api/src/main.py (lifespan)

async def upload_templates():
    """Upload operational templates to EHRBase on startup."""
    templates_dir = Path(__file__).parent.parent / "templates"
    for opt_file in templates_dir.glob("*.opt"):
        await ehrbase_client.upload_template(opt_file.read_text())
```

---

## Validation Rules

### Vital Signs Values

| Field | Type | Range | Required |
|-------|------|-------|----------|
| systolic | integer | 50-300 mmHg | If diastolic provided |
| diastolic | integer | 30-200 mmHg | If systolic provided |
| pulse_rate | integer | 20-300 bpm | No |
| recorded_at | datetime | Not in future | Yes |

### Business Rules

1. **At least one vital**: Must provide BP or pulse (or both)
2. **BP completeness**: If systolic provided, diastolic required (and vice versa)
3. **Timestamp**: Cannot be in the future
4. **Patient exists**: Patient must exist with valid EHR ID
5. **Encounter optional**: If provided, must be valid and belong to patient

---

## Security & Permissions

### Access Control
- All authenticated users can view vital signs
- Clinical staff can record vital signs
- Only admins can delete vital signs records

### Audit Trail
- All vital signs operations logged to AuditLog
- Composition UID stored for traceability
- EHRBase maintains its own versioning

---

## Testing Strategy

### Unit Tests (Backend)

```python
# api/tests/test_vital_signs.py

async def test_record_vital_signs_creates_composition():
    """Test that recording vitals creates EHRBase composition."""

async def test_record_vitals_requires_complete_bp():
    """Test validation: systolic requires diastolic."""

async def test_record_vitals_at_least_one_required():
    """Test validation: must provide BP or pulse."""

async def test_get_vitals_includes_openehr_metadata():
    """Test that response includes path mappings."""

async def test_get_raw_composition_flat_format():
    """Test fetching raw composition in FLAT format."""
```

### Frontend Tests

```typescript
// web/src/components/__tests__/VitalSignsChart.spec.ts

test('renders chart with BP and pulse data')
test('shows normal range reference lines')
test('highlights out-of-range values')
test('clicking point opens openEHR panel')
```

### E2E Tests

```typescript
// e2e/vital-signs.spec.ts

test('record vital signs and see in chart', async ({ page }) => {
  // Navigate to patient
  // Click "Record Vitals"
  // Fill form
  // Verify appears in chart and table
})

test('view openEHR metadata for reading', async ({ page }) => {
  // Navigate to patient vitals
  // Click openEHR button
  // Verify panel shows archetypes, paths
  // Copy path to clipboard
})
```

---

## Future Enhancements

### Additional Vital Signs (v2)
- Temperature (openEHR-EHR-OBSERVATION.body_temperature.v2)
- Respiratory rate (openEHR-EHR-OBSERVATION.respiration.v2)
- Oxygen saturation (openEHR-EHR-OBSERVATION.pulse_oximetry.v1)
- Weight/Height/BMI (openEHR-EHR-OBSERVATION.body_weight.v2, body_height.v2)

### Advanced Features
- Trend analysis and alerts
- Comparison with previous readings
- Export to CSV/PDF
- Integration with medical devices
- SMART on FHIR app launch

### openEHR Learning Mode
- Interactive archetype explorer
- AQL query builder with live preview
- Template designer integration

---

## Dependencies

### New NPM Packages

```json
{
  "chart.js": "^4.4.0",
  "vue-chartjs": "^5.3.0",
  "chartjs-adapter-date-fns": "^3.0.0"
}
```

### Template Files
- `api/templates/open-cis.vital-signs.v1.opt` (to be created)

---

## Open Questions

### Q1: Template Creation Approach
**Options:**
- A) Use Archetype Designer (web tool) to create OPT
- B) Hand-craft ADL/OPT XML
- C) Use existing public templates

**Recommendation:** Use Archetype Designer for visual design, export OPT.

### Q2: Store Vital Signs in App DB?
**Options:**
- A) Only in EHRBase (current plan)
- B) Mirror to app DB for faster queries
- C) Cache recent readings in app DB

**Recommendation:** Start with A (EHRBase only) for purity. Add caching later if needed.

### Q3: Chart Library
**Options:**
- A) Chart.js (lightweight, popular)
- B) Apache ECharts (more features, heavier)
- C) D3.js (most flexible, steeper learning curve)

**Recommendation:** Chart.js for simplicity and Vue integration.

---

## Success Criteria

**MVP is successful if:**
- ✅ Can record vital signs (BP + pulse) via UI
- ✅ Vital signs stored in EHRBase as compositions
- ✅ Chart displays readings over time
- ✅ openEHR metadata panel shows archetypes and paths
- ✅ Can view raw composition in FLAT format
- ✅ All operations complete in < 2 seconds
- ✅ Users understand how data maps to openEHR

---

## Change Log

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-01-03 | Open CIS Team | Initial PRD draft |
