# PRD-0006: CAVE Form (Allergies & Adverse Reactions)

**Version:** 1.0
**Date:** 2026-03-11
**Status:** Draft
**Owner:** Open CIS Project

---

## Executive Summary

Implement a CAVE (Latin: "beware") form for recording and displaying patient allergies, intolerances, and adverse reactions. CAVE information is critical safety data that must be visible whenever a clinician interacts with a patient, serving as a prominent warning system. This PRD defines the data model, openEHR integration, CRUD operations, and user interface for CAVE management.

---

## Problem Statement

**Current State:**
- No way to record patient allergies, intolerances, or adverse reactions
- No clinical safety warnings displayed on patient profiles
- No integration with the openEHR adverse reaction archetype
- Clinicians have no visibility into contraindications when viewing a patient

**User Personas:**
1. **Clinicians/Physicians** - Need to record known allergies and see warnings before prescribing
2. **Nurses** - Need to verify allergies at admission and before administering medications
3. **Pharmacists** - Need allergy data for drug interaction checking (future)
4. **Developers** - Need to understand openEHR allergy/adverse reaction modeling

---

## Goals & Success Metrics

### Goals
- Record and manage patient allergies, intolerances, and adverse reactions
- Display prominent CAVE warnings on the patient detail page
- Store allergy data as openEHR compositions in EHRBase using standard archetypes
- Support the full lifecycle: record, review, update, mark as resolved/refuted
- Provide openEHR transparency (composition paths, archetype mappings) consistent with vitals

### Success Metrics
- CAVE banner visible on patient detail page within 500ms of load
- 100% of CRUD operations available via UI
- Allergy data stored as valid openEHR compositions in EHRBase
- "No Known Allergies" (NKA) status can be explicitly recorded
- <2 second response time for all CAVE operations

---

## Domain Model

### Clinical Background

CAVE is a clinical safety concept used in European healthcare (especially German-speaking countries) as a prominent warning. It covers:

- **Allergies** - Immune-mediated reactions (e.g., penicillin allergy causing anaphylaxis)
- **Intolerances** - Non-immune adverse reactions (e.g., lactose intolerance, NSAID gastritis)
- **Adverse Reactions** - Any harmful/undesired effect from a substance (broader category)

### openEHR Archetype

The standard openEHR archetype for this domain is:

**`openEHR-EHR-EVALUATION.adverse_reaction_risk.v1`**

This archetype from the Clinical Knowledge Manager (CKM) models:
- The causative substance
- Overall reaction risk status (active, inactive, resolved)
- Criticality (low, high, indeterminate)
- Category (food, medication, environment, other)
- Individual reaction events with manifestations, severity, and certainty

### CAVE Entry Entity

**Core Attributes:**
- **Substance**: The agent causing the reaction (e.g., "Penicillin", "Peanuts", "Latex")
- **Category**: Classification of the substance
  - `medication` - Drug allergy/intolerance
  - `food` - Food allergy/intolerance
  - `environment` - Environmental allergen (pollen, dust, animal dander)
  - `other` - Other substances (contrast dye, latex, etc.)
- **Reaction Type**: Nature of the reaction
  - `allergy` - Immune-mediated (IgE or non-IgE)
  - `intolerance` - Non-immune adverse reaction
  - `unknown` - Type not yet determined
- **Criticality**: Worst-case assessment of potential harm
  - `low` - Non-life-threatening, localized reactions expected
  - `high` - Life-threatening or organ-threatening potential
  - `indeterminate` - Unable to assess
- **Status**: Clinical verification status
  - `active` - Currently active allergy/intolerance
  - `inactive` - No longer considered active (but not refuted)
  - `resolved` - Previously active, now resolved
  - `refuted` - Determined to be incorrect/not a true allergy
- **Onset Date**: When the allergy/reaction was first identified (optional)
- **Recorded Date**: When this entry was documented
- **Comment**: Free-text clinical notes

### Reaction Event (nested, 0..N per CAVE entry)
- **Manifestation**: Description of the reaction (e.g., "Urticaria", "Anaphylaxis", "Nausea")
- **Severity**: `mild`, `moderate`, `severe`
- **Certainty**: `suspected`, `likely`, `confirmed`
- **Date of Onset**: When this specific reaction occurred (optional)
- **Description**: Free-text details of the reaction event

### Special Status: No Known Allergies (NKA)

A dedicated mechanism to explicitly record that a patient has **no known allergies**. This is clinically distinct from "allergies not yet asked about" (unknown). The openEHR archetype `openEHR-EHR-EVALUATION.exclusion_global.v1` can model this.

---

## Data Model

### openEHR Template

A new openEHR template is required:

**Template: `Open CIS - Adverse Reaction List.v1`**

Composed of:
- `openEHR-EHR-COMPOSITION.adverse_reaction_list.v1` (root composition)
  - `openEHR-EHR-EVALUATION.adverse_reaction_risk.v1` (allergy entries)
  - `openEHR-EHR-EVALUATION.exclusion_global.v1` (NKA declaration)

> **Note:** The exact template design will depend on available archetypes in the CKM and what EHRBase supports. An ADR should be created during implementation to document the chosen template approach.

### TypeScript Types

```typescript
// web/src/types/cave.ts

export type CaveCategory = 'medication' | 'food' | 'environment' | 'other'
export type CaveReactionType = 'allergy' | 'intolerance' | 'unknown'
export type CaveCriticality = 'low' | 'high' | 'indeterminate'
export type CaveStatus = 'active' | 'inactive' | 'resolved' | 'refuted'
export type ReactionSeverity = 'mild' | 'moderate' | 'severe'
export type ReactionCertainty = 'suspected' | 'likely' | 'confirmed'

export interface ReactionEvent {
  manifestation: string
  severity: ReactionSeverity
  certainty: ReactionCertainty
  onset_date: string | null
  description: string | null
}

export interface CaveEntry {
  id: string // composition UID from EHRBase
  ehr_id: string
  patient_id: string
  substance: string
  category: CaveCategory
  reaction_type: CaveReactionType
  criticality: CaveCriticality
  status: CaveStatus
  onset_date: string | null
  recorded_date: string
  last_updated: string
  comment: string | null
  reactions: ReactionEvent[]
  // openEHR transparency
  composition_uid: string
  template_id: string
  archetype_ids: string[]
}

export interface CaveEntryCreate {
  patient_id: string
  substance: string
  category: CaveCategory
  reaction_type: CaveReactionType
  criticality: CaveCriticality
  status?: CaveStatus // defaults to 'active'
  onset_date?: string | null
  comment?: string | null
  reactions?: ReactionEvent[]
}

export interface CaveEntryUpdate {
  criticality?: CaveCriticality
  status?: CaveStatus
  comment?: string | null
  reactions?: ReactionEvent[]
}

export interface CaveSummary {
  patient_id: string
  total_active: number
  has_high_criticality: boolean
  has_nka_declaration: boolean
  entries: CaveEntry[]
}
```

### Python Schemas

```python
# api/src/cave/schemas.py

from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field


class CaveCategory(str, Enum):
    MEDICATION = "medication"
    FOOD = "food"
    ENVIRONMENT = "environment"
    OTHER = "other"


class CaveReactionType(str, Enum):
    ALLERGY = "allergy"
    INTOLERANCE = "intolerance"
    UNKNOWN = "unknown"


class CaveCriticality(str, Enum):
    LOW = "low"
    HIGH = "high"
    INDETERMINATE = "indeterminate"


class CaveStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    RESOLVED = "resolved"
    REFUTED = "refuted"


class ReactionSeverity(str, Enum):
    MILD = "mild"
    MODERATE = "moderate"
    SEVERE = "severe"


class ReactionCertainty(str, Enum):
    SUSPECTED = "suspected"
    LIKELY = "likely"
    CONFIRMED = "confirmed"


class ReactionEvent(BaseModel):
    manifestation: str = Field(..., max_length=200)
    severity: ReactionSeverity
    certainty: ReactionCertainty
    onset_date: datetime | None = None
    description: str | None = Field(None, max_length=500)


class CaveEntryCreate(BaseModel):
    patient_id: str
    substance: str = Field(..., min_length=1, max_length=200)
    category: CaveCategory
    reaction_type: CaveReactionType
    criticality: CaveCriticality
    status: CaveStatus = CaveStatus.ACTIVE
    onset_date: datetime | None = None
    comment: str | None = Field(None, max_length=1000)
    reactions: list[ReactionEvent] = Field(default_factory=list)


class CaveEntryUpdate(BaseModel):
    criticality: CaveCriticality | None = None
    status: CaveStatus | None = None
    comment: str | None = Field(None, max_length=1000)
    reactions: list[ReactionEvent] | None = None


class CaveEntryResponse(BaseModel):
    id: str
    ehr_id: str
    patient_id: str
    substance: str
    category: CaveCategory
    reaction_type: CaveReactionType
    criticality: CaveCriticality
    status: CaveStatus
    onset_date: datetime | None
    recorded_date: datetime
    last_updated: datetime
    comment: str | None
    reactions: list[ReactionEvent]
    # openEHR transparency
    composition_uid: str
    template_id: str
    archetype_ids: list[str]


class CaveSummaryResponse(BaseModel):
    patient_id: str
    total_active: int
    has_high_criticality: bool
    has_nka_declaration: bool
    entries: list[CaveEntryResponse]
```

---

## API Endpoints

### RESTful API Design

```
POST   /api/cave                          # Create CAVE entry
GET    /api/cave?patient_id={id}          # List CAVE entries for patient
GET    /api/cave/{composition_uid}        # Get single CAVE entry
PATCH  /api/cave/{composition_uid}        # Update CAVE entry
DELETE /api/cave/{composition_uid}        # Delete CAVE entry

GET    /api/cave/summary/{patient_id}     # Get CAVE summary (for banner)
POST   /api/cave/nka                      # Record "No Known Allergies"
```

### Query Parameters (for GET /api/cave)

- `patient_id` **(required)**: Filter by patient ID
- `status`: Filter by status (active, inactive, resolved, refuted)
- `category`: Filter by category
- `criticality`: Filter by criticality

### Request/Response Examples

**Create CAVE Entry:**
```http
POST /api/cave
Content-Type: application/json

{
  "patient_id": "cm123456789",
  "substance": "Penicillin",
  "category": "medication",
  "reaction_type": "allergy",
  "criticality": "high",
  "comment": "Confirmed by allergist Dr. Muller, 2024",
  "reactions": [
    {
      "manifestation": "Anaphylaxis",
      "severity": "severe",
      "certainty": "confirmed",
      "onset_date": "2024-03-15T00:00:00Z",
      "description": "Administered IV penicillin, developed anaphylaxis within 5 minutes"
    },
    {
      "manifestation": "Urticaria",
      "severity": "moderate",
      "certainty": "confirmed",
      "onset_date": "2023-01-10T00:00:00Z",
      "description": "Oral amoxicillin caused widespread hives"
    }
  ]
}

Response: 201 Created
{
  "id": "comp_abc123::open-cis::1",
  "ehr_id": "ehr_xyz789",
  "patient_id": "cm123456789",
  "substance": "Penicillin",
  "category": "medication",
  "reaction_type": "allergy",
  "criticality": "high",
  "status": "active",
  "onset_date": null,
  "recorded_date": "2026-03-11T10:00:00Z",
  "last_updated": "2026-03-11T10:00:00Z",
  "comment": "Confirmed by allergist Dr. Muller, 2024",
  "reactions": [...],
  "composition_uid": "comp_abc123::open-cis::1",
  "template_id": "Open CIS - Adverse Reaction List.v1",
  "archetype_ids": [
    "openEHR-EHR-EVALUATION.adverse_reaction_risk.v1"
  ]
}
```

**Get CAVE Summary (for patient banner):**
```http
GET /api/cave/summary/cm123456789

Response: 200 OK
{
  "patient_id": "cm123456789",
  "total_active": 2,
  "has_high_criticality": true,
  "has_nka_declaration": false,
  "entries": [
    {
      "substance": "Penicillin",
      "category": "medication",
      "criticality": "high",
      "status": "active",
      ...
    },
    {
      "substance": "Peanuts",
      "category": "food",
      "criticality": "high",
      "status": "active",
      ...
    }
  ]
}
```

**Record No Known Allergies:**
```http
POST /api/cave/nka
Content-Type: application/json

{
  "patient_id": "cm123456789"
}

Response: 201 Created
{
  "patient_id": "cm123456789",
  "has_nka_declaration": true
}
```

---

## User Interface Design

### CAVE Banner on Patient Detail Page

A prominent, always-visible banner at the top of the patient detail page:

**Patient has active allergies (high criticality):**
```
┌──────────────────────────────────────────────────────────┐
│ ⚠ CAVE                                     [Manage]     │
│ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐      │
│ │ ● Penicillin │ │ ● Peanuts    │ │ ● Latex      │      │
│ │   HIGH       │ │   HIGH       │ │   LOW        │      │
│ │   Medication │ │   Food       │ │   Other      │      │
│ └──────────────┘ └──────────────┘ └──────────────┘      │
└──────────────────────────────────────────────────────────┘
```
- Red/orange background for high criticality entries
- Yellow background for low criticality
- Each chip shows substance name, criticality, and category

**No Known Allergies recorded:**
```
┌──────────────────────────────────────────────────────────┐
│ ✓ CAVE: No Known Allergies                 [Manage]     │
│   Recorded: March 11, 2026                               │
└──────────────────────────────────────────────────────────┘
```
- Green/neutral background indicating NKA has been explicitly confirmed

**Allergies not yet assessed:**
```
┌──────────────────────────────────────────────────────────┐
│ ? CAVE: Not Yet Assessed                   [Record]     │
│   No allergy information has been recorded               │
└──────────────────────────────────────────────────────────┘
```
- Grey background, prompting clinician to assess

---

### CAVE Management Panel (Expanded View / Dialog)

Accessible via the "Manage" button on the banner:

```
┌──────────────────────────────────────────────────────────┐
│ CAVE - Allergies & Adverse Reactions     [+ Add Entry]  │
│ Patient: John Doe (MRN-12345)                           │
├──────────────────────────────────────────────────────────┤
│ Filters: [All ▼] [Active ▼] [All Categories ▼]         │
├──────────────────────────────────────────────────────────┤
│                                                          │
│ ● PENICILLIN                          Status: Active     │
│   Category: Medication | Criticality: HIGH               │
│   Type: Allergy (immune-mediated)                        │
│   Reactions:                                             │
│     - Anaphylaxis (severe, confirmed) - Mar 2024         │
│     - Urticaria (moderate, confirmed) - Jan 2023         │
│   Comment: Confirmed by allergist Dr. Muller, 2024       │
│   Recorded: Mar 11, 2026              [Edit] [Resolve]  │
│                                                          │
│ ─────────────────────────────────────────────────────── │
│                                                          │
│ ● PEANUTS                             Status: Active     │
│   Category: Food | Criticality: HIGH                     │
│   Type: Allergy (immune-mediated)                        │
│   Reactions:                                             │
│     - Angioedema (severe, confirmed) - Jun 2022          │
│   Recorded: Mar 11, 2026              [Edit] [Resolve]  │
│                                                          │
│ ─────────────────────────────────────────────────────── │
│                                                          │
│ ○ ASPIRIN                             Status: Resolved   │
│   Category: Medication | Criticality: LOW                │
│   Type: Intolerance                                      │
│   Reactions:                                             │
│     - GI upset (mild, suspected) - 2020                  │
│   Resolved: Feb 2026                  [Edit] [Reactivate]│
│                                                          │
├──────────────────────────────────────────────────────────┤
│ [Record "No Known Allergies"]                [Close]     │
└──────────────────────────────────────────────────────────┘
```

---

### Add/Edit CAVE Entry Dialog

```
┌──────────────────────────────────────────────────────────┐
│ Add Allergy / Adverse Reaction                     [×]  │
├──────────────────────────────────────────────────────────┤
│                                                          │
│ Substance *                                              │
│ [_______________________________]                        │
│                                                          │
│ Category *                                               │
│ ● Medication  ○ Food  ○ Environment  ○ Other             │
│                                                          │
│ Reaction Type *                                          │
│ ● Allergy (immune-mediated)                              │
│ ○ Intolerance (non-immune)                               │
│ ○ Unknown                                                │
│                                                          │
│ Criticality *                                            │
│ ○ Low    ● High    ○ Indeterminate                       │
│                                                          │
│ Onset Date                                               │
│ [__/__/____]                          (Optional)         │
│                                                          │
│ ── Reaction Events ──────────────────── [+ Add] ──      │
│                                                          │
│ Reaction #1                                    [Remove]  │
│ Manifestation *    [Anaphylaxis____________]             │
│ Severity *         ○ Mild  ○ Moderate  ● Severe          │
│ Certainty *        ○ Suspected  ○ Likely  ● Confirmed    │
│ Date               [03/15/2024]                          │
│ Description        [________________________________]    │
│                                                          │
│ ── Clinical Notes ──────────────────────────────────    │
│ [__________________________________________________]    │
│ [__________________________________________________]    │
│                                                          │
│                              [Cancel]  [Save Entry]      │
└──────────────────────────────────────────────────────────┘
```

---

## Validation Rules

### Required Fields
- `patient_id`: Must exist and not be deleted
- `substance`: 1-200 characters, must not duplicate an existing active entry for the same patient
- `category`: Must be valid CaveCategory enum
- `reaction_type`: Must be valid CaveReactionType enum
- `criticality`: Must be valid CaveCriticality enum

### Reaction Event Validation
- `manifestation`: Required, 1-200 characters
- `severity`: Must be valid ReactionSeverity enum
- `certainty`: Must be valid ReactionCertainty enum

### Business Rules
1. **No duplicate active substances**: Cannot have two active CAVE entries for the same substance on the same patient
2. **NKA conflicts**: Recording NKA when active allergies exist should warn the clinician and require confirmation
3. **NKA invalidation**: Adding a new allergy entry should automatically invalidate any existing NKA declaration
4. **Status transitions**: `active` → `inactive`/`resolved`/`refuted` are allowed; `refuted` → `active` requires new entry
5. **Substance cannot change**: Once recorded, the substance is immutable (create new entry instead)
6. **High criticality visual emphasis**: High criticality entries must be visually prominent

---

## openEHR Integration

### Template Design

Create a new OPT template for adverse reactions. The template should use:

- **Root Composition**: `openEHR-EHR-COMPOSITION.adverse_reaction_list.v1`
- **Content Archetype**: `openEHR-EHR-EVALUATION.adverse_reaction_risk.v1`
- **NKA Archetype**: `openEHR-EHR-EVALUATION.exclusion_global.v1`

### FLAT Composition Paths (Expected)

```
adverse_reaction_list/adverse_reaction_risk:0/substance|value
adverse_reaction_list/adverse_reaction_risk:0/substance|code
adverse_reaction_list/adverse_reaction_risk:0/status|code
adverse_reaction_list/adverse_reaction_risk:0/criticality|code
adverse_reaction_list/adverse_reaction_risk:0/category|code
adverse_reaction_list/adverse_reaction_risk:0/reaction:0/manifestation:0|value
adverse_reaction_list/adverse_reaction_risk:0/reaction:0/severity|code
adverse_reaction_list/adverse_reaction_risk:0/reaction:0/certainty|code
adverse_reaction_list/adverse_reaction_risk:0/reaction:0/onset_of_reaction|value
adverse_reaction_list/adverse_reaction_risk:0/reaction:0/reaction_description|value
adverse_reaction_list/adverse_reaction_risk:0/comment|value
```

> **Note:** Exact paths depend on the final OPT template. These will be confirmed during implementation and documented in the composition builder.

### AQL Query

```sql
SELECT
  c/uid/value as composition_uid,
  e/ehr_id/value as ehr_id,
  eval/data[at0001]/items[at0002]/value as substance,
  eval/data[at0001]/items[at0063]/value as status,
  eval/data[at0001]/items[at0101]/value as criticality,
  eval/data[at0001]/items[at0120]/value as category,
  eval/data[at0001]/items[at0009]/items[at0010]/value as manifestation,
  eval/data[at0001]/items[at0009]/items[at0021]/value as severity,
  eval/data[at0001]/items[at0009]/items[at0025]/value as certainty,
  eval/data[at0001]/items[at0009]/items[at0027]/value as onset_of_reaction,
  eval/data[at0001]/items[at0006]/value as comment
FROM EHR e
CONTAINS COMPOSITION c
CONTAINS EVALUATION eval[openEHR-EHR-EVALUATION.adverse_reaction_risk.v1]
WHERE e/ehr_id/value = :ehr_id
ORDER BY c/context/start_time DESC
```

### Transparency Features (consistent with vitals)

- Expose composition UID, template ID, archetype IDs in every response
- Provide path mappings from user-friendly fields to openEHR FLAT paths
- Support raw composition retrieval via existing `/api/observations/openehr/compositions/{uid}` endpoint

---

## Implementation Plan

### Phase 1: Backend Foundation (Week 1)

**Day 1-2: openEHR Template**
- [ ] Source or create adverse reaction OPT template
- [ ] Register template on EHRBase startup (extend `templates.py`)
- [ ] Verify template acceptance by EHRBase
- [ ] Document template choice in an ADR

**Day 3-4: API Module**
- [ ] Create `/api/src/cave/` module (router, service, schemas)
- [ ] Implement composition builder for adverse reactions (extend `openehr/compositions.py`)
- [ ] Implement AQL query for retrieving CAVE entries
- [ ] Add all CRUD endpoints
- [ ] Implement NKA recording endpoint

**Day 5: Testing**
- [ ] Unit tests for schema validation
- [ ] Integration tests with EHRBase
- [ ] Test NKA/allergy conflict logic

### Phase 2: Frontend Implementation (Week 2)

**Day 1-2: Core Components**
- [ ] Create `web/src/types/cave.ts` type definitions
- [ ] Create `web/src/stores/cave.ts` Pinia store
- [ ] Create `web/src/components/cave/CaveBanner.vue` (patient detail banner)
- [ ] Create `web/src/components/cave/CaveManagementPanel.vue`

**Day 3-4: Forms & Dialogs**
- [ ] Create `web/src/components/cave/CaveEntryDialog.vue` (add/edit)
- [ ] Implement reaction event sub-form (dynamic add/remove)
- [ ] Add client-side validation
- [ ] Create NKA recording flow

**Day 5: Integration**
- [ ] Integrate CaveBanner into PatientDetailPage
- [ ] Wire up all API calls
- [ ] Add loading/error states
- [ ] Test full flow end-to-end

### Phase 3: Polish & Safety (Week 3)

- [ ] Visual design refinement (color coding, iconography)
- [ ] Accessibility review (ARIA labels, screen reader support for warnings)
- [ ] Add CAVE data to synthetic seeding script
- [ ] Manual QA and edge case testing
- [ ] Performance optimization (summary endpoint caching)

---

## Security & Permissions

### Access Control
- All authenticated users can **view** CAVE information (safety-critical data)
- Clinical staff (CLINICIAN, NURSE) can **create and update** CAVE entries
- Only clinicians can **refute** an allergy (requires clinical judgment)
- Only admins can **delete** CAVE entries (compositions in EHRBase)

### Data Protection
- Allergy data is PHI - standard protections apply
- Audit all CAVE operations (create, update, status change, delete)
- Never suppress CAVE warnings based on user role

---

## Testing Strategy

### Unit Tests (Backend)

```python
# api/tests/test_cave.py

async def test_create_cave_entry():
    """Test creating a new allergy entry"""

async def test_create_cave_entry_duplicate_substance():
    """Test that duplicate active entries for same substance are rejected"""

async def test_update_cave_criticality():
    """Test updating criticality of existing entry"""

async def test_resolve_cave_entry():
    """Test marking an allergy as resolved"""

async def test_refute_cave_entry():
    """Test marking an allergy as refuted"""

async def test_record_nka():
    """Test recording No Known Allergies"""

async def test_nka_invalidated_on_new_entry():
    """Test that NKA is invalidated when new allergy is added"""

async def test_get_cave_summary():
    """Test summary endpoint returns correct counts and flags"""

async def test_cave_entry_with_reactions():
    """Test creating entry with multiple reaction events"""
```

### Frontend Tests

```typescript
// web/src/__tests__/cave.test.ts

test('CaveBanner shows red for high criticality', () => {})
test('CaveBanner shows NKA status correctly', () => {})
test('CaveBanner shows not-assessed prompt', () => {})
test('CaveEntryDialog validates required fields', () => {})
test('CaveEntryDialog prevents duplicate substances', () => {})
test('CaveManagementPanel filters by status', () => {})
test('Reaction events can be added and removed', () => {})
```

---

## Future Enhancements (v2.0)

1. **Substance Autocomplete** - Integrate with a terminology service (SNOMED CT, ATC) for standardized substance coding
2. **Drug Interaction Checking** - Cross-reference CAVE entries with medication orders to flag contraindications
3. **Allergy Alerts in Prescribing** - Pop-up warnings when ordering medications matching known allergies
4. **Cross-Reactivity Warnings** - Flag potential cross-reactivity (e.g., penicillin ↔ cephalosporins)
5. **Patient-Facing View** - Allow patients to review their allergy list via a patient portal
6. **FHIR AllergyIntolerance Export** - Map openEHR data to FHIR R4 AllergyIntolerance resource for interoperability
7. **Barcode/Wristband Integration** - Include CAVE summary on patient wristband prints

---

## Open Questions & Decisions

### Question 1: Template Approach
**Options:**
- A) Source an existing OPT template from the openEHR CKM / Apperta Foundation
- B) Build a custom template using the standard archetypes
- C) Use a simplified template with only the core fields for MVP

**Recommendation:** Start with C for MVP. Use the standard `adverse_reaction_risk.v1` archetype but limit the template to core fields (substance, category, criticality, status, reactions). Expand in v2.0.

### Question 2: Substance Coding
**Options:**
- A) Free-text substance entry (MVP)
- B) Autocomplete from a local substance list
- C) Full terminology integration (SNOMED CT)

**Recommendation:** Start with A (free-text) for MVP. Add B (local list of common allergens) as a quick follow-up. Defer C to v2.0.

### Question 3: One Composition per Entry vs. One Composition per Patient
**Options:**
- A) Each CAVE entry is a separate composition in EHRBase
- B) All CAVE entries for a patient are in a single "adverse reaction list" composition

**Recommendation:** Use B (single composition per patient) as this aligns with the `adverse_reaction_list` composition archetype and makes it easier to query all allergies at once. Updates replace the full composition.

### Question 4: Where to Display CAVE Banner
**Options:**
- A) Only on Patient Detail Page (MVP)
- B) On all pages when a patient context is active
- C) As a global notification bar

**Recommendation:** Start with A for MVP. Consider B when the application has more patient-context-aware views.

---

## Dependencies

### New openEHR Artifacts
- Adverse reaction OPT template (to be sourced or created)
- Archetypes: `adverse_reaction_risk.v1`, `exclusion_global.v1`, `adverse_reaction_list.v1`

### Existing Dependencies
- EHRBase (composition storage and AQL queries)
- FastAPI (API endpoints)
- Prisma (patient registry lookup)
- Pinia (frontend state management)
- shadcn-vue (UI components)

### No New NPM/Python Packages Expected
- All required functionality is available in existing dependencies

---

## Success Criteria

**MVP is successful if:**
- ✅ Can create CAVE entries with substance, category, criticality, and reactions
- ✅ CAVE banner displays on patient detail page with visual severity coding
- ✅ Can update status (active → resolved/refuted)
- ✅ Can record "No Known Allergies" explicitly
- ✅ NKA is invalidated when a new allergy is added
- ✅ All data stored as valid openEHR compositions in EHRBase
- ✅ openEHR transparency (paths, archetypes) available in responses
- ✅ All operations complete in <2 seconds
- ✅ High criticality entries are visually prominent and unmissable

---

## Change Log

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-03-11 | Open CIS Team | Initial PRD draft |
