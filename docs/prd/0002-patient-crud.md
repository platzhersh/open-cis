# PRD-0002: Patient CRUD Operations

**Version:** 1.0
**Date:** 2026-01-03
**Status:** Draft
**Owner:** Open CIS Project

---

## Executive Summary

Complete the patient management functionality by implementing missing CRUD operations. Currently, patient creation and reading are partially implemented, but the frontend lacks a creation form, update functionality is incomplete, and deletion is entirely missing. This PRD defines the complete patient lifecycle management with proper EHR integration, validation, and user experience.

---

## Problem Statement

**Current State:**
- ✅ **Create:** API endpoint exists, but frontend has non-functional "Add Patient" button
- ✅ **Read:** List and detail views work properly
- ⚠️ **Update:** API endpoint exists (`PATCH /api/patients/{id}`), but no frontend UI
- ❌ **Delete:** No implementation at API or frontend level

**Pain Points:**
- Users cannot add patients through the UI (must use API directly)
- No way to correct patient demographic errors after creation
- No mechanism to remove test patients or handle data cleanup
- MRN duplicates cause cryptic database errors instead of user-friendly validation
- EHR lifecycle unclear when patient is deleted

**User Personas:**
1. **Registration Clerk** - Needs to register new patients, correct typos in demographics
2. **Clinical Staff** - Needs to view patient information, update demographics
3. **System Administrator** - Needs to delete test patients, manage data quality
4. **Developer/QA** - Needs to create/delete test patients during development

---

## Goals & Success Metrics

### Goals
- Enable complete patient lifecycle management through the UI
- Ensure data integrity between app database and EHRBase
- Provide clear validation feedback for duplicate MRN
- Define and implement safe patient deletion strategy
- Improve user experience with responsive forms and confirmations

### Success Metrics
- 100% of CRUD operations available via UI (create, read, update, delete)
- <2 second response time for patient operations
- Zero data inconsistencies between PatientRegistry and EHRBase EHRs
- Duplicate MRN validation prevents database errors (100% caught at UI level)
- User testing: 5/5 users can create, update, and delete patients without confusion

---

## Current Implementation Analysis

### Existing API Endpoints
```
POST   /api/patients              ✅ Create patient + EHR
GET    /api/patients              ✅ List patients (pagination)
GET    /api/patients/{id}         ✅ Get patient by ID
GET    /api/patients/mrn/{mrn}    ✅ Get patient by MRN
PATCH  /api/patients/{id}         ✅ Update demographics
DELETE /api/patients/{id}         ❌ NOT IMPLEMENTED
```

### Existing Prisma Schema
```prisma
model PatientRegistry {
  id         String    @id @default(cuid())
  ehrId      String    @unique      // EHRBase EHR ID
  mrn        String    @unique      // Medical Record Number
  givenName  String
  familyName String
  birthDate  DateTime?
  createdAt  DateTime  @default(now())
  updatedAt  DateTime  @updatedAt
}
```

### Existing Frontend Pages
- `PatientListPage.vue` - Table view with non-functional "Add Patient" button
- `PatientDetailPage.vue` - Read-only detail view, no edit/delete actions

### Existing Pinia Store Methods
- `fetchPatients()` ✅
- `fetchPatient(id)` ✅
- `createPatient(data)` ✅ (defined but unused)
- `updatePatient(id, data)` ❌ Missing
- `deletePatient(id)` ❌ Missing

---

## Feature Requirements

### Phase 1: Patient Creation (P0 - Must Have)

#### User Stories
- As a registration clerk, I want to add a new patient so I can register them in the system
- As a user, I want to see validation errors before submitting so I don't waste time
- As a user, I want clear feedback when MRN already exists so I can choose a different one

#### Functional Requirements

**1.1 Patient Creation Form**
- **Trigger:** Click "Add Patient" button on PatientListPage
- **UI Component:** Modal dialog (shadcn-vue Dialog component)
- **Form Fields:**
  - **MRN** (Medical Record Number)
    - Input type: Text
    - Required: Yes
    - Validation:
      - Min length: 3 characters
      - Max length: 20 characters
      - Pattern: Alphanumeric + hyphens (e.g., "MRN-12345")
      - Unique: Check via API before submission
    - Error messages:
      - "MRN is required"
      - "MRN must be 3-20 characters"
      - "MRN must be alphanumeric"
      - "MRN already exists"

  - **Given Name** (First Name)
    - Input type: Text
    - Required: Yes
    - Validation: Min 1 character, Max 50 characters
    - Error: "Given name is required"

  - **Family Name** (Last Name)
    - Input type: Text
    - Required: Yes
    - Validation: Min 1 character, Max 50 characters
    - Error: "Family name is required"

  - **Birth Date**
    - Input type: Date picker
    - Required: No
    - Validation:
      - Must be past date (not future)
      - Reasonable range (1900 - today)
    - Error: "Birth date cannot be in the future"

**1.2 Form Behavior**
- **Real-time validation:** Show field errors on blur or submit attempt
- **MRN uniqueness check:**
  - Debounced API call to `GET /api/patients/mrn/{mrn}` after 500ms of typing
  - Show loading spinner during check
  - Display "✓ Available" or "✗ Already exists" indicator
- **Submit button:** Disabled until form is valid
- **Loading state:** Show spinner in button, disable form during submission
- **Success:**
  - Close modal
  - Show toast: "Patient {name} created successfully"
  - Refresh patient list
  - Navigate to new patient detail page (optional)
- **Error:**
  - Show error message in modal (do not close)
  - Toast: "Failed to create patient: {error message}"

**1.3 EHR Creation**
- Automatically create EHR in EHRBase on patient creation (current behavior)
- Display EHR ID in success message or detail page
- Handle EHRBase errors gracefully:
  - If EHR creation fails, rollback patient creation
  - Show user-friendly error: "Unable to create electronic health record. Please try again."

**1.4 API Enhancements**
- Add `/api/patients/mrn/{mrn}/exists` endpoint for quick validation
  - Returns `{ "exists": true/false }`
  - Does not return patient data (privacy)
  - Publicly accessible (no auth required for this check)

**1.5 Technical Implementation**
```vue
<!-- web/src/pages/patients/PatientListPage.vue -->
<script setup>
import { ref } from 'vue'
import { usePatientStore } from '@/stores/patientStore'
import PatientCreateDialog from '@/components/patients/PatientCreateDialog.vue'

const showCreateDialog = ref(false)
const patientStore = usePatientStore()

const handlePatientCreated = () => {
  showCreateDialog.value = false
  patientStore.fetchPatients()
}
</script>

<template>
  <Button @click="showCreateDialog = true">Add Patient</Button>
  <PatientCreateDialog
    :open="showCreateDialog"
    @close="showCreateDialog = false"
    @created="handlePatientCreated"
  />
</template>
```

```typescript
// web/src/components/patients/PatientCreateDialog.vue
interface PatientCreateForm {
  mrn: string
  givenName: string
  familyName: string
  birthDate: string | null
}

const form = ref<PatientCreateForm>({
  mrn: '',
  givenName: '',
  familyName: '',
  birthDate: null
})

const mrnExists = ref<boolean | null>(null)
const checkingMrn = ref(false)

// Debounced MRN uniqueness check
watchDebounced(
  () => form.value.mrn,
  async (newMrn) => {
    if (newMrn.length < 3) return
    checkingMrn.value = true
    const result = await patientStore.checkMrnExists(newMrn)
    mrnExists.value = result
    checkingMrn.value = false
  },
  { debounce: 500 }
)

const handleSubmit = async () => {
  if (mrnExists.value) return

  try {
    loading.value = true
    await patientStore.createPatient(form.value)
    toast.success(`Patient ${form.value.givenName} ${form.value.familyName} created`)
    emit('created')
  } catch (error) {
    toast.error(`Failed to create patient: ${error.message}`)
  } finally {
    loading.value = false
  }
}
```

---

### Phase 2: Patient Update (P0 - Must Have)

#### User Stories
- As a registration clerk, I want to correct typos in patient demographics
- As a user, I want to update birth date if initially unknown
- As a user, I want clear confirmation that changes were saved

#### Functional Requirements

**2.1 Patient Edit Mode**
- **Trigger:** Click "Edit" button on PatientDetailPage
- **UI Change:** Convert read-only fields to editable inputs
- **Editable Fields:**
  - Given Name (text input)
  - Family Name (text input)
  - Birth Date (date picker)
- **Non-editable Fields:**
  - MRN (displayed as read-only badge)
  - EHR ID (displayed as read-only)
  - Patient ID (displayed as read-only)
  - Created At (displayed as read-only)

**2.2 Edit Form Behavior**
- **Toggle edit mode:**
  - "Edit" button → Shows "Save" and "Cancel" buttons
  - "Cancel" → Reverts changes, returns to read-only mode
  - "Save" → Validates and submits changes
- **Validation:** Same as creation form for editable fields
- **Dirty state tracking:**
  - Disable "Save" if no changes made
  - Show "Unsaved changes" warning if navigating away
- **Optimistic update:**
  - Update UI immediately on successful save
  - Revert on error

**2.3 Update API**
- Use existing `PATCH /api/patients/{id}` endpoint
- Accept partial updates (only changed fields)
- Return updated patient data
- Handle conflicts (e.g., concurrent edits)

**2.4 Success/Error Handling**
- **Success:**
  - Toast: "Patient updated successfully"
  - Exit edit mode, show updated data
  - Update `updatedAt` timestamp in UI
- **Error:**
  - Toast: "Failed to update patient: {error}"
  - Remain in edit mode, preserve user input
  - Show field-specific errors if validation fails

**2.5 Technical Implementation**
```vue
<!-- web/src/pages/patients/PatientDetailPage.vue -->
<script setup>
const isEditing = ref(false)
const editForm = ref<PatientUpdateForm | null>(null)

const startEditing = () => {
  isEditing.value = true
  editForm.value = { ...patient.value }
}

const cancelEditing = () => {
  if (hasUnsavedChanges.value) {
    if (!confirm('Discard unsaved changes?')) return
  }
  isEditing.value = false
  editForm.value = null
}

const saveChanges = async () => {
  try {
    await patientStore.updatePatient(patient.value.id, editForm.value)
    toast.success('Patient updated successfully')
    isEditing.value = false
  } catch (error) {
    toast.error(`Failed to update: ${error.message}`)
  }
}
</script>

<template>
  <div v-if="!isEditing">
    <Button @click="startEditing">Edit</Button>
    <!-- Read-only fields -->
  </div>
  <div v-else>
    <Button @click="saveChanges" :disabled="!hasChanges">Save</Button>
    <Button @click="cancelEditing" variant="outline">Cancel</Button>
    <!-- Editable form fields -->
  </div>
</template>
```

```typescript
// web/src/stores/patientStore.ts
async updatePatient(id: string, data: PatientUpdateForm) {
  const response = await api.patch(`/api/patients/${id}`, data)

  // Update in local state
  const index = this.patients.findIndex(p => p.id === id)
  if (index !== -1) {
    this.patients[index] = response.data
  }
  if (this.currentPatient?.id === id) {
    this.currentPatient = response.data
  }

  return response.data
}
```

---

### Phase 3: Patient Deletion (P1 - Should Have)

#### User Stories
- As an admin, I want to delete test patients to clean up my environment
- As a user, I want to understand what happens to EHR data when deleting a patient
- As a user, I want protection against accidental deletion

#### Functional Requirements

**3.1 Delete Trigger**
- **Location:** PatientDetailPage
- **UI Element:** "Delete Patient" button in danger zone section
- **Access Control:** Only visible to users with `admin` role
- **Visual Design:** Red/destructive button variant, placed at bottom of page

**3.2 Delete Confirmation Dialog**
- **Two-step confirmation:**
  1. Initial confirmation dialog
  2. Type patient MRN to confirm (for high-risk deletion)
- **Warning messages:**
  - "This action cannot be undone"
  - "The patient's EHR and all associated compositions will be marked as deleted"
  - "Type the patient's MRN to confirm: {MRN}"
- **Buttons:**
  - "Cancel" (default focus)
  - "Delete Patient" (enabled only when MRN typed correctly)

**3.3 Deletion Strategy**

**Option A: Soft Delete (Recommended)**
- Add `deletedAt: DateTime?` field to PatientRegistry schema
- Set `deletedAt = now()` on deletion
- Filter out deleted patients from list queries by default
- Keep EHR in EHRBase (do not delete)
- Add `GET /api/patients?includeDeleted=true` for admins
- **Pros:** Data preservation, auditability, reversible
- **Cons:** Database growth, complexity

**Option B: Hard Delete**
- Permanently delete PatientRegistry record
- Attempt to delete EHR from EHRBase (if API supports)
- **Pros:** Clean database, simple
- **Cons:** Data loss, not reversible, EHRBase may not support EHR deletion

**Option C: Prevent Deletion if Compositions Exist**
- Check if patient has any compositions in EHRBase
- If yes: Show error "Cannot delete patient with existing clinical data"
- If no: Allow deletion (soft or hard)
- **Pros:** Protects clinical data
- **Cons:** Users cannot delete patients with any data

**Recommendation:** **Option A (Soft Delete)** for initial implementation. Add Option C validation as additional safety layer.

**3.4 API Implementation**
```python
# api/src/patients/router.py
@router.delete("/{patient_id}", status_code=204)
async def delete_patient(
    patient_id: str,
    current_user: CurrentUser,
    db: PrismaClient = Depends(get_db)
) -> None:
    """Soft delete a patient (requires admin role)."""
    # Check permissions
    if not current_user.is_admin:
        raise HTTPException(403, "Admin role required")

    # Check if patient exists
    patient = await service.get_patient(db, patient_id)
    if not patient:
        raise HTTPException(404, "Patient not found")

    # Optional: Check for compositions
    composition_count = await ehrbase_client.count_compositions(patient.ehr_id)
    if composition_count > 0:
        raise HTTPException(
            400,
            f"Cannot delete patient with {composition_count} existing compositions"
        )

    # Soft delete
    await service.delete_patient(db, patient_id)
    return None
```

```python
# api/src/patients/service.py
async def delete_patient(db: PrismaClient, patient_id: str) -> None:
    """Soft delete patient by setting deletedAt timestamp."""
    await db.patientregistry.update(
        where={"id": patient_id},
        data={"deletedAt": datetime.utcnow()}
    )
```

**3.5 Schema Migration**
```prisma
// api/prisma/schema.prisma
model PatientRegistry {
  id         String    @id @default(cuid())
  ehrId      String    @unique
  mrn        String    @unique
  givenName  String
  familyName String
  birthDate  DateTime?
  createdAt  DateTime  @default(now())
  updatedAt  DateTime  @updatedAt
  deletedAt  DateTime? @map("deleted_at")  // NEW FIELD

  @@map("patient_registry")
}
```

**3.6 Frontend Implementation**
```vue
<!-- web/src/pages/patients/PatientDetailPage.vue -->
<script setup>
const showDeleteDialog = ref(false)
const deletionMrn = ref('')

const handleDelete = async () => {
  if (deletionMrn.value !== patient.value.mrn) {
    toast.error('MRN does not match')
    return
  }

  try {
    await patientStore.deletePatient(patient.value.id)
    toast.success('Patient deleted successfully')
    router.push('/patients')
  } catch (error) {
    if (error.response?.status === 400) {
      toast.error('Cannot delete patient with existing clinical data')
    } else {
      toast.error(`Failed to delete patient: ${error.message}`)
    }
  }
}
</script>

<template>
  <section class="danger-zone">
    <h3>Danger Zone</h3>
    <Button variant="destructive" @click="showDeleteDialog = true">
      Delete Patient
    </Button>
  </section>

  <AlertDialog :open="showDeleteDialog" @close="showDeleteDialog = false">
    <AlertDialogContent>
      <AlertDialogHeader>
        <AlertDialogTitle>Delete Patient</AlertDialogTitle>
        <AlertDialogDescription>
          This action cannot be undone. The patient's EHR and all associated
          data will be marked as deleted.
        </AlertDialogDescription>
      </AlertDialogHeader>

      <div class="my-4">
        <Label>Type the patient's MRN to confirm: <strong>{{ patient.mrn }}</strong></Label>
        <Input v-model="deletionMrn" placeholder="Enter MRN" />
      </div>

      <AlertDialogFooter>
        <AlertDialogCancel>Cancel</AlertDialogCancel>
        <AlertDialogAction
          @click="handleDelete"
          :disabled="deletionMrn !== patient.mrn"
          variant="destructive"
        >
          Delete Patient
        </AlertDialogAction>
      </AlertDialogFooter>
    </AlertDialogContent>
  </AlertDialog>
</template>
```

**3.7 List Query Update**
```python
# api/src/patients/service.py
async def list_patients(
    db: PrismaClient,
    skip: int = 0,
    limit: int = 20,
    include_deleted: bool = False
) -> list[PatientResponse]:
    """List patients with soft delete filtering."""
    where_clause = {} if include_deleted else {"deletedAt": None}

    patients = await db.patientregistry.find_many(
        where=where_clause,
        skip=skip,
        take=limit,
        order_by={"createdAt": "desc"}
    )
    return patients
```

---

## User Interface Design

### Design Principles
1. **Progressive Disclosure:** Simple list → Detail view → Edit mode
2. **Confirmations:** Require explicit confirmation for destructive actions
3. **Validation Feedback:** Real-time, field-level, user-friendly messages
4. **Accessibility:** Keyboard navigation, screen reader support, focus management
5. **Responsiveness:** Mobile-friendly forms and tables

### Component Hierarchy

```
PatientListPage
├── PageHeader
│   ├── Title: "Patients"
│   └── Action: "Add Patient" button
├── PatientTable
│   ├── Columns: MRN, Name, Birth Date, Actions
│   ├── Row Actions: "View" link
│   └── Empty State: "No patients yet. Add your first patient."
└── PatientCreateDialog (modal)
    ├── Form Fields: MRN, Given Name, Family Name, Birth Date
    ├── Validation Indicators
    └── Actions: Cancel, Create

PatientDetailPage
├── PageHeader
│   ├── Breadcrumb: Patients > {Patient Name}
│   └── Actions: "Edit" button (or "Save"/"Cancel" in edit mode)
├── DemographicsSection
│   ├── Read-only Mode: Display fields
│   └── Edit Mode: Input fields with validation
├── SystemInfoSection
│   └── Read-only: Patient ID, EHR ID, Created At, Updated At
├── ClinicalDataSection (future)
│   └── Encounters, Compositions, etc.
└── DangerZone (admin only)
    └── "Delete Patient" button
```

### Visual Design

**Patient List Table:**
```
┌──────────────────────────────────────────────────────────────┐
│ Patients                                   [+ Add Patient]    │
├──────────────────────────────────────────────────────────────┤
│ MRN        │ Name              │ Birth Date    │ Actions     │
├──────────────────────────────────────────────────────────────┤
│ MRN-12345  │ John Doe          │ 1990-05-15    │ [View]      │
│ MRN-67890  │ Jane Smith        │ 1985-08-22    │ [View]      │
│ MRN-11111  │ Bob Johnson       │ Not provided  │ [View]      │
└──────────────────────────────────────────────────────────────┘
```

**Patient Create Dialog:**
```
┌────────────────────────────────────────┐
│ Add New Patient                    [×] │
├────────────────────────────────────────┤
│                                        │
│ MRN *                                  │
│ [MRN-_____] [✓ Available]             │
│                                        │
│ Given Name *                           │
│ [_______________]                      │
│                                        │
│ Family Name *                          │
│ [_______________]                      │
│                                        │
│ Birth Date                             │
│ [📅 Select date...]                    │
│                                        │
├────────────────────────────────────────┤
│                     [Cancel] [Create]  │
└────────────────────────────────────────┘
```

**Patient Detail (Edit Mode):**
```
┌────────────────────────────────────────────────────┐
│ ← Patients / John Doe               [Save] [Cancel]│
├────────────────────────────────────────────────────┤
│ Demographics                                        │
│                                                     │
│ MRN: MRN-12345 (read-only)                         │
│                                                     │
│ Given Name *                                        │
│ [John___________]                                   │
│                                                     │
│ Family Name *                                       │
│ [Doe____________]                                   │
│                                                     │
│ Birth Date                                          │
│ [📅 1990-05-15]                                     │
│                                                     │
├────────────────────────────────────────────────────┤
│ System Information (read-only)                      │
│ Patient ID: abc123                                  │
│ EHR ID: 12345678-abcd-...                          │
│ Created: Jan 1, 2026 10:30 AM                      │
│ Updated: Jan 3, 2026 2:15 PM                       │
├────────────────────────────────────────────────────┤
│ ⚠ Danger Zone (admin only)                         │
│ [Delete Patient]                                    │
└────────────────────────────────────────────────────┘
```

---

## Technical Implementation

### Frontend Changes

**New Components:**
```
web/src/components/patients/
├── PatientCreateDialog.vue      # Create patient modal
├── PatientEditForm.vue          # Editable demographics form
├── PatientDeleteDialog.vue      # Delete confirmation dialog
└── PatientFormFields.vue        # Shared form fields component
```

**Updated Pages:**
```
web/src/pages/patients/
├── PatientListPage.vue          # Wire up "Add Patient" button
└── PatientDetailPage.vue        # Add edit mode + delete action
```

**Store Updates:**
```typescript
// web/src/stores/patientStore.ts

interface PatientStore {
  // Existing
  patients: Patient[]
  currentPatient: Patient | null
  fetchPatients(): Promise<void>
  fetchPatient(id: string): Promise<void>
  createPatient(data: PatientCreateForm): Promise<Patient>

  // New
  checkMrnExists(mrn: string): Promise<boolean>
  updatePatient(id: string, data: PatientUpdateForm): Promise<Patient>
  deletePatient(id: string): Promise<void>
}
```

**Type Definitions:**
```typescript
// web/src/types/patient.ts

export interface Patient {
  id: string
  ehrId: string
  mrn: string
  givenName: string
  familyName: string
  birthDate: string | null
  createdAt: string
  updatedAt: string
  deletedAt?: string | null
}

export interface PatientCreateForm {
  mrn: string
  givenName: string
  familyName: string
  birthDate: string | null
}

export interface PatientUpdateForm {
  givenName?: string
  familyName?: string
  birthDate?: string | null
}
```

---

### Backend Changes

**New Endpoints:**
```python
# api/src/patients/router.py

# New endpoint
@router.get("/mrn/{mrn}/exists")
async def check_mrn_exists(mrn: str, db: PrismaClient = Depends(get_db)) -> dict:
    """Check if MRN already exists."""
    exists = await service.mrn_exists(db, mrn)
    return {"exists": exists}

# New endpoint
@router.delete("/{patient_id}", status_code=204)
async def delete_patient(
    patient_id: str,
    current_user: CurrentUser,
    db: PrismaClient = Depends(get_db)
) -> None:
    """Soft delete a patient."""
    # Implementation in service layer
```

**Service Layer Updates:**
```python
# api/src/patients/service.py

async def mrn_exists(db: PrismaClient, mrn: str) -> bool:
    """Check if MRN is already in use."""
    patient = await db.patientregistry.find_first(
        where={"mrn": mrn, "deletedAt": None}
    )
    return patient is not None

async def delete_patient(db: PrismaClient, patient_id: str) -> None:
    """Soft delete patient."""
    await db.patientregistry.update(
        where={"id": patient_id},
        data={"deletedAt": datetime.utcnow()}
    )

async def list_patients(
    db: PrismaClient,
    skip: int = 0,
    limit: int = 20,
    include_deleted: bool = False
) -> list[dict]:
    """List patients with optional soft delete filter."""
    where_clause = {} if include_deleted else {"deletedAt": None}
    # ... rest of implementation
```

**Prisma Schema Migration:**
```prisma
model PatientRegistry {
  id         String    @id @default(cuid())
  ehrId      String    @unique @map("ehr_id")
  mrn        String    @unique
  givenName  String    @map("given_name")
  familyName String    @map("family_name")
  birthDate  DateTime? @map("birth_date")
  createdAt  DateTime  @default(now()) @map("created_at")
  updatedAt  DateTime  @updatedAt @map("updated_at")
  deletedAt  DateTime? @map("deleted_at")  // NEW

  @@map("patient_registry")
}
```

**Migration Command:**
```bash
cd api && prisma migrate dev --name add_soft_delete_to_patients
```

---

## Validation Rules

### MRN Validation
- **Required:** Yes
- **Format:** Alphanumeric + hyphens only
- **Length:** 3-20 characters
- **Uniqueness:** Must not exist in database (case-insensitive)
- **Regex:** `^[A-Za-z0-9-]{3,20}$`

### Given Name Validation
- **Required:** Yes
- **Length:** 1-50 characters
- **Allowed:** Letters, spaces, hyphens, apostrophes
- **Regex:** `^[A-Za-z\s'-]{1,50}$`

### Family Name Validation
- **Required:** Yes
- **Length:** 1-50 characters
- **Allowed:** Letters, spaces, hyphens, apostrophes
- **Regex:** `^[A-Za-z\s'-]{1,50}$`

### Birth Date Validation
- **Required:** No
- **Format:** ISO 8601 date (YYYY-MM-DD)
- **Range:** 1900-01-01 to today
- **Not allowed:** Future dates

---

## Error Handling

### API Error Responses

| Status Code | Scenario | Response Body | User Message |
|-------------|----------|---------------|--------------|
| 400 | Validation error | `{"detail": "Invalid MRN format"}` | "Invalid MRN format. Use alphanumeric characters and hyphens only." |
| 400 | Duplicate MRN | `{"detail": "MRN already exists"}` | "This MRN is already in use. Please choose a different one." |
| 400 | Delete with compositions | `{"detail": "Cannot delete patient with existing compositions"}` | "Cannot delete patient with existing clinical data." |
| 403 | Unauthorized delete | `{"detail": "Admin role required"}` | "You do not have permission to delete patients." |
| 404 | Patient not found | `{"detail": "Patient not found"}` | "Patient not found." |
| 500 | EHR creation failed | `{"detail": "Failed to create EHR in EHRBase"}` | "Unable to create electronic health record. Please try again." |
| 503 | EHRBase unavailable | `{"detail": "EHRBase service unavailable"}` | "Clinical data service is temporarily unavailable. Please try again later." |

### Frontend Error Display

**Field-level errors:**
- Show below input field in red text
- Icon: ⚠️ or ❌
- Clear when field is corrected

**Form-level errors:**
- Show at top of form in Alert component
- Icon: ⚠️
- Dismissible

**Toast notifications:**
- Success: Green, auto-dismiss after 3 seconds
- Error: Red, auto-dismiss after 5 seconds (or user dismisses)
- Info: Blue, auto-dismiss after 4 seconds

---

## Security & Permissions

### Access Control

| Operation | Endpoint | Required Role | Notes |
|-----------|----------|---------------|-------|
| Create Patient | POST /api/patients | `user` or `admin` | All authenticated users |
| List Patients | GET /api/patients | `user` or `admin` | All authenticated users |
| View Patient | GET /api/patients/{id} | `user` or `admin` | All authenticated users |
| Update Patient | PATCH /api/patients/{id} | `user` or `admin` | All authenticated users |
| Delete Patient | DELETE /api/patients/{id} | `admin` only | Destructive action |
| Check MRN Exists | GET /api/patients/mrn/{mrn}/exists | Public | No auth required for UX |

### Data Protection
- **MRN:** Considered PII, log access, do not expose in error messages
- **Birth Date:** Considered PHI, redact in logs
- **Audit Trail:** Log all create/update/delete operations with user ID
- **Soft Delete:** Preserve data for audit, exclude from normal queries

### Implementation
```python
# api/src/auth/permissions.py
from enum import Enum

class Role(Enum):
    USER = "user"
    ADMIN = "admin"

def require_role(required_role: Role):
    """Decorator to enforce role-based access."""
    def decorator(func):
        async def wrapper(*args, current_user: CurrentUser, **kwargs):
            if current_user.role not in [required_role, Role.ADMIN]:
                raise HTTPException(403, "Insufficient permissions")
            return await func(*args, current_user=current_user, **kwargs)
        return wrapper
    return decorator

# Usage
@router.delete("/{patient_id}")
@require_role(Role.ADMIN)
async def delete_patient(...):
    ...
```

---

## Testing Strategy

### Unit Tests (Backend)

**Test Coverage:**
- ✅ Create patient with valid data
- ✅ Create patient with duplicate MRN (should fail)
- ✅ Create patient with invalid MRN format (should fail)
- ✅ Update patient demographics
- ✅ Update patient with no changes (should be no-op)
- ✅ Delete patient (soft delete)
- ✅ List patients excludes soft-deleted by default
- ✅ List patients with includeDeleted=true shows all
- ✅ MRN exists check returns true/false correctly

**Test File:**
```python
# api/tests/test_patients.py

async def test_create_patient_success():
    response = await client.post("/api/patients", json={
        "mrn": "MRN-TEST-001",
        "given_name": "John",
        "family_name": "Doe",
        "birth_date": "1990-01-01"
    })
    assert response.status_code == 201
    assert response.json()["mrn"] == "MRN-TEST-001"
    assert "ehr_id" in response.json()

async def test_create_patient_duplicate_mrn():
    # Create first patient
    await client.post("/api/patients", json={"mrn": "MRN-001", ...})

    # Attempt duplicate
    response = await client.post("/api/patients", json={"mrn": "MRN-001", ...})
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"]

async def test_soft_delete_patient():
    # Create patient
    create_response = await client.post("/api/patients", json={...})
    patient_id = create_response.json()["id"]

    # Delete
    delete_response = await client.delete(f"/api/patients/{patient_id}")
    assert delete_response.status_code == 204

    # Verify not in list
    list_response = await client.get("/api/patients")
    assert patient_id not in [p["id"] for p in list_response.json()]

    # Verify in list with includeDeleted=true
    all_response = await client.get("/api/patients?includeDeleted=true")
    assert patient_id in [p["id"] for p in all_response.json()]
```

### Unit Tests (Frontend)

**Test Coverage:**
- ✅ PatientCreateDialog renders form fields
- ✅ Form validation shows errors for invalid inputs
- ✅ MRN uniqueness check called on input
- ✅ Submit button disabled until form valid
- ✅ Successful creation closes dialog and refreshes list
- ✅ Edit mode toggles correctly
- ✅ Save button disabled when no changes
- ✅ Delete confirmation requires MRN match

**Test File:**
```typescript
// web/src/components/patients/PatientCreateDialog.test.ts

describe('PatientCreateDialog', () => {
  it('validates MRN format', async () => {
    const { getByLabelText, getByText } = render(PatientCreateDialog)
    const mrnInput = getByLabelText('MRN')

    await userEvent.type(mrnInput, 'invalid mrn!')
    await waitFor(() => {
      expect(getByText('MRN must be alphanumeric')).toBeInTheDocument()
    })
  })

  it('checks MRN uniqueness', async () => {
    const checkMrnExists = vi.fn().mockResolvedValue(true)
    const { getByLabelText, getByText } = render(PatientCreateDialog, {
      props: { checkMrnExists }
    })

    await userEvent.type(getByLabelText('MRN'), 'MRN-12345')

    await waitFor(() => {
      expect(checkMrnExists).toHaveBeenCalledWith('MRN-12345')
      expect(getByText('Already exists')).toBeInTheDocument()
    })
  })
})
```

### Integration Tests

**Scenarios:**
- ✅ Full patient creation flow (API + EHRBase)
- ✅ Update patient and verify EHR unchanged
- ✅ Delete patient with compositions (should fail)
- ✅ Delete patient without compositions (should succeed)

### E2E Tests (Playwright)

**Test Scenarios:**
```typescript
// e2e/patients.spec.ts

test('create, update, and delete patient', async ({ page }) => {
  await page.goto('/patients')

  // Create
  await page.click('text=Add Patient')
  await page.fill('input[name="mrn"]', 'E2E-TEST-001')
  await page.fill('input[name="givenName"]', 'Test')
  await page.fill('input[name="familyName"]', 'User')
  await page.click('button:has-text("Create")')

  await expect(page.locator('text=Patient Test User created')).toBeVisible()

  // View
  await page.click('text=E2E-TEST-001')
  await expect(page.locator('h1:has-text("Test User")')).toBeVisible()

  // Edit
  await page.click('button:has-text("Edit")')
  await page.fill('input[name="givenName"]', 'Updated')
  await page.click('button:has-text("Save")')
  await expect(page.locator('text=Patient updated successfully')).toBeVisible()

  // Delete (admin only)
  await page.click('button:has-text("Delete Patient")')
  await page.fill('input[placeholder="Enter MRN"]', 'E2E-TEST-001')
  await page.click('button:has-text("Delete Patient")')
  await expect(page).toHaveURL('/patients')
})
```

### Manual Testing Checklist

**Patient Creation:**
- [ ] Form opens when clicking "Add Patient"
- [ ] MRN validation shows errors for invalid formats
- [ ] MRN uniqueness check prevents duplicates
- [ ] All required fields validated
- [ ] Birth date picker works correctly
- [ ] Success toast appears after creation
- [ ] Patient appears in list immediately
- [ ] EHR ID is displayed in detail view

**Patient Update:**
- [ ] Edit button toggles to edit mode
- [ ] All editable fields become inputs
- [ ] MRN remains read-only
- [ ] Save button disabled when no changes
- [ ] Cancel reverts changes
- [ ] Unsaved changes warning works
- [ ] Success toast appears after update
- [ ] Updated data displays correctly

**Patient Deletion:**
- [ ] Delete button only visible to admins
- [ ] Confirmation dialog appears
- [ ] Cannot delete without typing MRN
- [ ] Deleting patient with compositions shows error
- [ ] Deleting patient without compositions succeeds
- [ ] Deleted patient removed from list
- [ ] Redirect to list page after deletion

---

## Implementation Timeline

### Week 1: Patient Creation
**Days 1-2:**
- [ ] Create `PatientCreateDialog.vue` component
- [ ] Add form validation logic
- [ ] Implement MRN uniqueness check
- [ ] Wire up "Add Patient" button in `PatientListPage.vue`

**Days 3-4:**
- [ ] Add `GET /api/patients/mrn/{mrn}/exists` endpoint
- [ ] Add `checkMrnExists()` to patient store
- [ ] Test creation flow end-to-end
- [ ] Fix bugs and polish UX

**Day 5:**
- [ ] Write unit tests for creation
- [ ] Write E2E test for creation
- [ ] Code review and merge

### Week 2: Patient Update
**Days 1-2:**
- [ ] Add edit mode toggle to `PatientDetailPage.vue`
- [ ] Create `PatientEditForm.vue` component
- [ ] Implement dirty state tracking
- [ ] Add save/cancel buttons

**Days 3-4:**
- [ ] Add `updatePatient()` to patient store
- [ ] Implement optimistic updates
- [ ] Test update flow end-to-end
- [ ] Handle concurrent edit scenarios

**Day 5:**
- [ ] Write unit tests for updates
- [ ] Write E2E test for editing
- [ ] Code review and merge

### Week 3: Patient Deletion
**Days 1-2:**
- [ ] Add `deletedAt` field to Prisma schema
- [ ] Run migration: `prisma migrate dev --name add_soft_delete`
- [ ] Update `list_patients()` to filter soft-deleted
- [ ] Add `DELETE /api/patients/{id}` endpoint

**Days 3-4:**
- [ ] Create `PatientDeleteDialog.vue` component
- [ ] Add delete button to detail page (admin only)
- [ ] Implement MRN confirmation logic
- [ ] Add `deletePatient()` to patient store
- [ ] Test deletion flow end-to-end

**Day 5:**
- [ ] Write unit tests for deletion
- [ ] Write E2E test for deletion
- [ ] Test admin permission enforcement
- [ ] Code review and merge

### Week 4: Polish & Documentation
- [ ] Add loading skeletons
- [ ] Improve error messages
- [ ] Add keyboard shortcuts
- [ ] Write user documentation
- [ ] Create demo video/GIF
- [ ] Final QA pass

---

## Success Criteria

**MVP is successful if:**
- ✅ Users can create patients via UI (not just API)
- ✅ Users can update patient demographics
- ✅ Admins can delete patients safely
- ✅ MRN duplicates prevented at UI level (zero database errors)
- ✅ All operations complete in <2 seconds
- ✅ Zero data inconsistencies between PatientRegistry and EHRBase
- ✅ 5/5 users successfully complete create/update/delete tasks
- ✅ Zero critical bugs in first week of use

**Long-term success:**
- 100% of patient operations happen via UI (not curl/Postman)
- <5 support tickets related to patient management per month
- Patient onboarding time reduced by 50%

---

## Future Considerations

### v2.0 Features
- **Advanced Search:** Filter by name, MRN, birth date range
- **Bulk Operations:** Import patients from CSV, bulk update
- **Patient Merge:** Combine duplicate patient records
- **Audit Log UI:** View who created/updated/deleted patients and when
- **Patient Photos:** Upload and display patient photos
- **Family Relationships:** Link patients (parent/child, spouse, etc.)
- **Contact Information:** Phone, email, address fields
- **Insurance Information:** Link to insurance providers
- **Preferred Language:** Support for multilingual patients
- **Emergency Contacts:** Store next of kin information

### Integration Opportunities
- **HL7 ADT Messages:** Sync patient data with hospital ADT system
- **FHIR Patient Resource:** Export patients as FHIR Patient resources
- **Identity Verification:** Integrate with identity verification services
- **Duplicate Detection:** Use fuzzy matching to detect potential duplicates
- **EHR Viewer:** Inline EHRBase data viewer on patient detail page

### Performance Optimizations
- **Pagination:** Server-side pagination for large patient lists
- **Virtual Scrolling:** For lists with 1000+ patients
- **Search Indexing:** Full-text search on patient names
- **Caching:** Redis cache for frequently accessed patients

---

## Open Questions & Risks

### Open Questions

1. **MRN Format:** Should we enforce a specific MRN format (e.g., always "MRN-" prefix)?
   - **Recommendation:** Allow flexible format initially, make configurable later

2. **Deceased Patients:** Should we add a "deceased" field and prevent modifications?
   - **Recommendation:** Add in v2.0 with proper workflow

3. **Patient Merging:** What happens when duplicate patients are discovered?
   - **Recommendation:** Manual merge tool in v2.0, prevent duplicates in v1.0

4. **EHR Deletion:** Does EHRBase support deleting EHRs? Should we even try?
   - **Recommendation:** No, use soft delete only. EHRs are permanent by design.

### Risks

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| EHRBase doesn't support EHR deletion | Medium | High | Use soft delete, keep EHR intact |
| Users accidentally delete patients | High | Medium | Two-step confirmation, MRN typing, admin-only |
| MRN format varies by organization | Medium | Medium | Make format configurable via settings |
| Performance issues with large patient lists | Medium | Low | Implement pagination early |
| Concurrent edits cause data loss | High | Low | Optimistic locking, show conflict warnings |

---

## Dependencies

### New NPM Packages
```json
{
  "@vueuse/core": "^10.7.0",           // For watchDebounced, useConfirmDialog
  "date-fns": "^3.0.0"                  // Date formatting and validation
}
```

### Existing Dependencies (No Changes)
- shadcn-vue components (Dialog, Alert, Input, Button, etc.)
- Pinia for state management
- Vue Router for navigation
- Axios/Fetch for API calls

---

## References

- [openEHR EHR Information Model](https://specifications.openehr.org/releases/RM/latest/ehr.html) - EHR lifecycle concepts
- [HL7 FHIR Patient Resource](https://www.hl7.org/fhir/patient.html) - Standard patient demographics
- [Medical Record Number Best Practices](https://www.himss.org/resources/medical-record-number-mrn) - MRN format guidance
- [EHRBase REST API Docs](https://docs.ehrbase.org/) - EHR management endpoints
- [shadcn-vue Documentation](https://www.shadcn-vue.com/) - UI component library

---

## Appendix A: API Request/Response Examples

### Create Patient
```http
POST /api/patients
Content-Type: application/json

{
  "mrn": "MRN-12345",
  "given_name": "John",
  "family_name": "Doe",
  "birth_date": "1990-05-15"
}

Response: 201 Created
{
  "id": "cm123456789",
  "ehr_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "mrn": "MRN-12345",
  "given_name": "John",
  "family_name": "Doe",
  "birth_date": "1990-05-15",
  "created_at": "2026-01-03T10:30:00Z",
  "updated_at": "2026-01-03T10:30:00Z"
}
```

### Update Patient
```http
PATCH /api/patients/cm123456789
Content-Type: application/json

{
  "given_name": "Jonathan",
  "birth_date": "1990-05-16"
}

Response: 200 OK
{
  "id": "cm123456789",
  "ehr_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "mrn": "MRN-12345",
  "given_name": "Jonathan",
  "family_name": "Doe",
  "birth_date": "1990-05-16",
  "created_at": "2026-01-03T10:30:00Z",
  "updated_at": "2026-01-03T14:45:00Z"
}
```

### Delete Patient
```http
DELETE /api/patients/cm123456789

Response: 204 No Content
```

### Check MRN Exists
```http
GET /api/patients/mrn/MRN-12345/exists

Response: 200 OK
{
  "exists": true
}
```

---

## Change Log

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-01-03 | Open CIS Team | Initial PRD draft |
