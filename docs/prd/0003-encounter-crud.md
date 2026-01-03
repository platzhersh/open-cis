# PRD-0003: Encounter CRUD Operations

**Version:** 1.0
**Date:** 2026-01-03
**Status:** Draft
**Owner:** Open CIS Project

---

## Executive Summary

Implement complete encounter management functionality to track patient visits, consultations, and clinical events. Encounters are the fundamental unit of care delivery in a CIS, representing a single interaction between a patient and healthcare provider. This PRD defines the data model, CRUD operations, and user interface for encounter management.

---

## Problem Statement

**Current State:**
- No way to record patient encounters (visits, consultations, admissions)
- Patient detail page shows "Recent Encounters: Coming soon"
- Cannot track when patients were seen, by whom, or for what reason
- No foundation for linking clinical data (vital signs, diagnoses, procedures) to encounters

**User Personas:**
1. **Clinical Staff** - Needs to create encounters when patients arrive, document visit details
2. **Physicians** - Needs to review patient encounter history, add clinical notes
3. **Administrators** - Needs to track encounter statistics, billing data
4. **Developers/QA** - Needs to create test encounters for development

---

## Goals & Success Metrics

### Goals
- Enable tracking of all patient interactions (visits, admissions, teleconsults)
- Provide clear encounter history on patient detail page
- Support different encounter types and statuses
- Lay groundwork for future clinical documentation (notes, orders, etc.)

### Success Metrics
- 100% of CRUD operations available via UI
- <2 second response time for encounter operations
- Encounter list displays most recent encounters first
- Filter encounters by patient, type, status, date range
- Soft delete with audit trail

---

## Domain Model

### Encounter Entity

An encounter represents a single interaction between a patient and the healthcare system.

**Core Attributes:**
- **ID**: Unique identifier (auto-generated)
- **Patient ID**: Foreign key to patient
- **Type**: Encounter type (ambulatory, emergency, inpatient, virtual, etc.)
- **Status**: Current status (planned, in-progress, finished, cancelled)
- **Start Time**: When the encounter began
- **End Time**: When the encounter ended (null if ongoing)
- **Reason**: Chief complaint or reason for visit
- **Provider Name**: Name of the primary provider (simplified for MVP)
- **Location**: Where the encounter took place
- **Created At**: Timestamp of record creation
- **Updated At**: Timestamp of last update
- **Deleted At**: Soft delete timestamp (null if active)

### Encounter Types (Based on FHIR/openEHR)
- **ambulatory**: Outpatient visit or consultation
- **emergency**: Emergency department visit
- **inpatient**: Hospital admission/stay
- **virtual**: Telemedicine/remote consultation
- **home**: Home health visit
- **field**: Mobile/community health encounter

### Encounter Status
- **planned**: Scheduled but not yet started
- **in-progress**: Currently ongoing
- **finished**: Completed normally
- **cancelled**: Cancelled before or during encounter

---

## Data Model

### Prisma Schema

```prisma
model Encounter {
  id          String    @id @default(cuid())
  patientId   String    @map("patient_id")
  type        String    // ambulatory, emergency, inpatient, virtual, home, field
  status      String    // planned, in-progress, finished, cancelled
  startTime   DateTime  @map("start_time")
  endTime     DateTime? @map("end_time")
  reason      String?   // Chief complaint or reason for visit
  providerName String?  @map("provider_name") // Simplified for MVP
  location    String?   // Department, room, clinic name
  createdAt   DateTime  @default(now()) @map("created_at")
  updatedAt   DateTime  @updatedAt @map("updated_at")
  deletedAt   DateTime? @map("deleted_at")

  patient     PatientRegistry @relation(fields: [patientId], references: [id], onDelete: Cascade)

  @@map("encounters")
  @@index([patientId])
  @@index([startTime])
  @@index([status])
}

// Update PatientRegistry to include relation
model PatientRegistry {
  // ... existing fields
  encounters  Encounter[]
}
```

### TypeScript Types

```typescript
// web/src/types/encounter.ts

export type EncounterType =
  | 'ambulatory'
  | 'emergency'
  | 'inpatient'
  | 'virtual'
  | 'home'
  | 'field'

export type EncounterStatus =
  | 'planned'
  | 'in-progress'
  | 'finished'
  | 'cancelled'

export interface Encounter {
  id: string
  patient_id: string
  type: EncounterType
  status: EncounterStatus
  start_time: string // ISO 8601
  end_time: string | null
  reason: string | null
  provider_name: string | null
  location: string | null
  created_at: string
  updated_at: string
}

export interface EncounterCreate {
  patient_id: string
  type: EncounterType
  status: EncounterStatus
  start_time: string
  end_time?: string | null
  reason?: string | null
  provider_name?: string | null
  location?: string | null
}

export interface EncounterUpdate {
  type?: EncounterType
  status?: EncounterStatus
  start_time?: string
  end_time?: string | null
  reason?: string | null
  provider_name?: string | null
  location?: string | null
}
```

### Python Schemas

```python
# api/src/encounters/schemas.py

from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field


class EncounterType(str, Enum):
    AMBULATORY = "ambulatory"
    EMERGENCY = "emergency"
    INPATIENT = "inpatient"
    VIRTUAL = "virtual"
    HOME = "home"
    FIELD = "field"


class EncounterStatus(str, Enum):
    PLANNED = "planned"
    IN_PROGRESS = "in-progress"
    FINISHED = "finished"
    CANCELLED = "cancelled"


class EncounterCreate(BaseModel):
    patient_id: str
    type: EncounterType
    status: EncounterStatus
    start_time: datetime
    end_time: datetime | None = None
    reason: str | None = None
    provider_name: str | None = Field(None, max_length=100)
    location: str | None = Field(None, max_length=100)


class EncounterUpdate(BaseModel):
    type: EncounterType | None = None
    status: EncounterStatus | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None
    reason: str | None = None
    provider_name: str | None = Field(None, max_length=100)
    location: str | None = Field(None, max_length=100)


class EncounterResponse(BaseModel):
    id: str
    patient_id: str
    type: EncounterType
    status: EncounterStatus
    start_time: datetime
    end_time: datetime | None
    reason: str | None
    provider_name: str | None
    location: str | None
    created_at: datetime
    updated_at: datetime
```

---

## API Endpoints

### RESTful API Design

```
POST   /api/encounters                   # Create encounter
GET    /api/encounters                   # List all encounters (with filters)
GET    /api/encounters/{id}              # Get encounter by ID
PATCH  /api/encounters/{id}              # Update encounter
DELETE /api/encounters/{id}              # Soft delete encounter

GET    /api/patients/{patient_id}/encounters  # List patient's encounters
```

### Query Parameters (for GET /api/encounters)

- `patient_id`: Filter by patient ID
- `type`: Filter by encounter type
- `status`: Filter by status
- `start_date`: Filter encounters starting after this date
- `end_date`: Filter encounters starting before this date
- `skip`: Pagination offset (default: 0)
- `limit`: Page size (default: 100, max: 1000)
- `include_deleted`: Include soft-deleted encounters (default: false)

### Request/Response Examples

**Create Encounter:**
```http
POST /api/encounters
Content-Type: application/json

{
  "patient_id": "cm123456789",
  "type": "ambulatory",
  "status": "in-progress",
  "start_time": "2026-01-03T10:00:00Z",
  "reason": "Annual physical examination",
  "provider_name": "Dr. Jane Smith",
  "location": "Clinic A, Room 101"
}

Response: 201 Created
{
  "id": "enc_abc123",
  "patient_id": "cm123456789",
  "type": "ambulatory",
  "status": "in-progress",
  "start_time": "2026-01-03T10:00:00Z",
  "end_time": null,
  "reason": "Annual physical examination",
  "provider_name": "Dr. Jane Smith",
  "location": "Clinic A, Room 101",
  "created_at": "2026-01-03T10:00:00Z",
  "updated_at": "2026-01-03T10:00:00Z"
}
```

**Update Encounter (mark as finished):**
```http
PATCH /api/encounters/enc_abc123
Content-Type: application/json

{
  "status": "finished",
  "end_time": "2026-01-03T10:45:00Z"
}

Response: 200 OK
{
  "id": "enc_abc123",
  "status": "finished",
  "end_time": "2026-01-03T10:45:00Z",
  ...
}
```

---

## User Interface Design

### Encounter List Page (`/encounters`)

**Layout:**
```
┌────────────────────────────────────────────────────┐
│ Encounters                    [+ New Encounter]    │
├────────────────────────────────────────────────────┤
│ Filters:                                           │
│ [Patient ▼] [Type ▼] [Status ▼] [Date Range]     │
├────────────────────────────────────────────────────┤
│ Patient       │ Type      │ Status   │ Date/Time   │
│──────────────────────────────────────────────────  │
│ John Doe      │ Ambulatory│ Finished │ Jan 3, 10am │
│ Jane Smith    │ Emergency │ In Prog  │ Jan 3, 11am │
│ Bob Johnson   │ Virtual   │ Planned  │ Jan 4, 2pm  │
└────────────────────────────────────────────────────┘
```

**Features:**
- Table view with key encounter details
- Filters for patient, type, status, date range
- Sort by start time (most recent first)
- Click row to view encounter details
- "New Encounter" button (primary action)
- Pagination for large lists

---

### Patient Detail Page - Recent Encounters Section

Replace "Coming soon" placeholder with actual encounter list:

```
Recent Encounters (5)                    [View All]
────────────────────────────────────────────────────
Jan 3, 2026 10:00 AM - Ambulatory - Dr. Smith
Annual physical examination
[View Details]

Jan 1, 2026 2:00 PM - Virtual - Dr. Jones
Follow-up consultation
[View Details]

Dec 28, 2025 9:00 AM - Emergency - Dr. Williams
Chest pain
[View Details]
```

**Features:**
- Show 5 most recent encounters
- Display type, provider, reason
- "View All" link to filtered encounter list
- "View Details" for individual encounter
- Add quick "New Encounter" button

---

### Encounter Detail Page (`/encounters/{id}`)

```
┌────────────────────────────────────────────────────┐
│ ← Back to Encounters          [Edit] [Delete]     │
├────────────────────────────────────────────────────┤
│ Encounter Details                                  │
│                                                    │
│ Patient: John Doe (MRN-12345)  [View Patient]     │
│ Type: Ambulatory Outpatient Visit                 │
│ Status: Finished                                   │
│                                                    │
│ Timeline                                           │
│ Started: Jan 3, 2026 10:00 AM                     │
│ Ended: Jan 3, 2026 10:45 AM                       │
│ Duration: 45 minutes                               │
│                                                    │
│ Clinical Information                               │
│ Reason: Annual physical examination                │
│ Provider: Dr. Jane Smith                           │
│ Location: Clinic A, Room 101                       │
│                                                    │
│ System Information                                 │
│ Encounter ID: enc_abc123                           │
│ Created: Jan 3, 2026 10:00 AM                     │
│ Updated: Jan 3, 2026 10:45 AM                     │
│                                                    │
│ [Clinical Documentation - Coming Soon]             │
│ [Diagnoses - Coming Soon]                          │
│ [Procedures - Coming Soon]                         │
└────────────────────────────────────────────────────┘
```

---

### Create/Edit Encounter Dialog

**Create Mode:**
```
Add New Encounter                              [×]
───────────────────────────────────────────────────
Patient *
[Search patients...              ▼]

Encounter Type *
● Ambulatory    ○ Emergency  ○ Inpatient
○ Virtual       ○ Home       ○ Field

Status *
● Planned  ● In Progress  ○ Finished  ○ Cancelled

Start Date & Time *
[01/03/2026] [10:00 AM]

End Date & Time
[01/03/2026] [10:45 AM]  (Optional for ongoing)

Reason for Visit
[____________________________________]

Provider Name
[____________________________________]

Location
[____________________________________]

                           [Cancel] [Create]
```

**Edit Mode:**
- Same form, pre-filled with existing data
- Cannot change patient (business rule)
- Button changes to "Save Changes"

---

## Validation Rules

### Required Fields
- `patient_id`: Must exist and not be deleted
- `type`: Must be valid EncounterType enum
- `status`: Must be valid EncounterStatus enum
- `start_time`: Must be provided, cannot be in far future (max 1 year ahead)

### Optional Fields
- `end_time`: If provided, must be >= start_time
- `reason`: Max 500 characters
- `provider_name`: Max 100 characters
- `location`: Max 100 characters

### Business Rules
1. **Patient must exist**: Cannot create encounter for non-existent patient
2. **Cannot change patient**: Once created, patient_id is immutable
3. **End time >= Start time**: Logical constraint
4. **Finished encounters must have end_time**: If status = finished, end_time required
5. **Cancelled encounters**: Can optionally have end_time (cancellation time)

---

## Implementation Plan

### Week 1: Backend Foundation

**Day 1-2: Data Model**
- [ ] Create Prisma migration for Encounter model
- [ ] Add relation to PatientRegistry
- [ ] Run migration and verify schema
- [ ] Update Python types/schemas

**Day 3-4: API Endpoints**
- [ ] Create `/api/src/encounters/` module
- [ ] Implement service layer (CRUD operations)
- [ ] Implement router with all endpoints
- [ ] Add validation and error handling
- [ ] Write unit tests

**Day 5: Integration**
- [ ] Add `/api/patients/{id}/encounters` endpoint
- [ ] Test cascade delete (patient deletion)
- [ ] Integration tests with Prisma

### Week 2: Frontend Implementation

**Day 1-2: Core Components**
- [ ] Create encounter types/interfaces
- [ ] Implement encounter store (Pinia)
- [ ] Create EncounterListPage component
- [ ] Create EncounterDetailPage component

**Day 3-4: Dialogs & Forms**
- [ ] Create EncounterCreateDialog component
- [ ] Create EncounterEditDialog component
- [ ] Add validation logic
- [ ] Implement delete confirmation

**Day 5: Patient Integration**
- [ ] Add "Recent Encounters" section to PatientDetailPage
- [ ] Add "New Encounter" button with patient pre-selected
- [ ] Add "View All Encounters" link with patient filter
- [ ] Update navigation/routes

### Week 3: Polish & Testing

- [ ] Add filtering and pagination
- [ ] Improve UI/UX (loading states, animations)
- [ ] Write E2E tests (Playwright)
- [ ] Manual QA testing
- [ ] Bug fixes and performance optimization

---

## Security & Permissions

### Access Control
- All authenticated users can view encounters
- Clinical staff can create/update encounters
- Only admins can delete encounters (soft delete)

### Data Protection
- Reason for visit is PHI - handle securely
- Audit all encounter operations
- Soft delete preserves data for compliance

---

## Testing Strategy

### Unit Tests (Backend)
```python
# api/tests/test_encounters.py

async def test_create_encounter():
    """Test creating a new encounter"""

async def test_update_encounter():
    """Test updating encounter details"""

async def test_delete_encounter_soft_delete():
    """Test soft delete preserves data"""

async def test_finished_encounter_requires_end_time():
    """Test validation: finished status requires end_time"""

async def test_end_time_after_start_time():
    """Test validation: end_time >= start_time"""

async def test_list_encounters_by_patient():
    """Test filtering encounters by patient"""
```

### E2E Tests (Frontend)
```typescript
// e2e/encounters.spec.ts

test('create encounter for patient', async ({ page }) => {
  // Navigate to patient detail
  // Click "New Encounter"
  // Fill form and submit
  // Verify encounter appears in list
})

test('edit encounter and mark as finished', async ({ page }) => {
  // Open encounter detail
  // Click Edit
  // Update status and end_time
  // Verify updates
})

test('delete encounter', async ({ page }) => {
  // Open encounter
  // Click delete
  // Confirm deletion
  // Verify removed from list
})
```

---

## Future Enhancements (v2.0)

1. **Clinical Documentation**
   - SOAP notes (Subjective, Objective, Assessment, Plan)
   - Progress notes
   - Discharge summaries

2. **Diagnosis Tracking**
   - Link diagnoses (ICD-10) to encounters
   - Primary vs secondary diagnoses

3. **Procedure Documentation**
   - Procedures performed during encounter
   - CPT codes for billing

4. **Provider Management**
   - Separate Provider entity
   - Provider schedules and availability

5. **Location/Department Hierarchy**
   - Organization structure
   - Department/clinic management

6. **Encounter Templates**
   - Pre-defined encounter types with default fields
   - Specialty-specific templates

7. **Real-time Collaboration**
   - Multiple users working on same encounter
   - WebSocket updates

8. **Billing Integration**
   - Generate claims from encounters
   - Track encounter costs

---

## Open Questions & Decisions

### Question 1: Provider Data Model
**Options:**
- A) Simple string field (current design - MVP)
- B) Separate Provider entity with relation
- C) Reference to User entity

**Decision:** Start with A (string field) for MVP. Migrate to B in v2.0.

### Question 2: Encounter Class vs Type
**Options:**
- A) Single "type" field (current design)
- B) Separate "class" (inpatient/outpatient/emergency) and "type" (routine/urgent/walkin)

**Decision:** Use A for simplicity. FHIR uses class+type, but for MVP a single type is sufficient.

### Question 3: How to handle overlapping encounters?
**Scenario:** Patient has in-progress encounter, staff creates another

**Options:**
- A) Allow multiple in-progress encounters (current design)
- B) Prevent overlapping encounters (add validation)
- C) Auto-finish previous encounter when creating new one

**Decision:** Use A for flexibility. Some legitimate cases exist (e.g., phone consult during inpatient stay).

---

## Dependencies

### New NPM Packages
```json
{
  "date-fns": "^3.0.0"  // Already added in patient PRD
}
```

### Existing Dependencies
- Prisma (database ORM)
- FastAPI (Python API framework)
- Pinia (state management)
- shadcn-vue (UI components)

---

## Success Criteria

**MVP is successful if:**
- ✅ Can create encounters via UI
- ✅ Can view encounter list filtered by patient
- ✅ Can edit encounter details (type, status, times)
- ✅ Can soft delete encounters
- ✅ Patient detail page shows recent encounters
- ✅ All operations complete in <2 seconds
- ✅ Validation prevents invalid data (end < start, etc.)
- ✅ 5/5 users can manage encounters without confusion

---

## Change Log

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-01-03 | Open CIS Team | Initial PRD draft |
