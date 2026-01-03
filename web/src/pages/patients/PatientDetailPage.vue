<script setup lang="ts">
import { onMounted, ref, computed, watch } from 'vue'
import { useRoute, useRouter, RouterLink } from 'vue-router'
import { DialogRoot, DialogPortal, DialogOverlay, DialogContent, DialogTitle, DialogDescription, DialogClose } from 'radix-vue'
import { X, Loader2, Pencil, Trash2, AlertTriangle, Plus } from 'lucide-vue-next'
import { usePatientStore } from '@/stores/patient'
import { useEncounterStore } from '@/stores/encounter'
import type { PatientUpdate } from '@/types'

const route = useRoute()
const router = useRouter()
const store = usePatientStore()
const encounterStore = useEncounterStore()

const patientId = route.params.id as string

// Edit mode state
const isEditing = ref(false)
const editForm = ref<PatientUpdate>({})
const editErrors = ref<Record<string, string>>({})
const saving = ref(false)

// Delete dialog state
const showDeleteDialog = ref(false)
const deleteConfirmMrn = ref('')
const deleting = ref(false)

onMounted(() => {
  store.fetchPatient(patientId)
  encounterStore.fetchEncounters(patientId)
})

// Get recent encounters (max 5)
const recentEncounters = computed(() => {
  return encounterStore.encounters.slice(0, 5)
})

// Format encounter type for display
const formatEncounterType = (type: string) => {
  const types: Record<string, string> = {
    ambulatory: 'Ambulatory',
    emergency: 'Emergency',
    inpatient: 'Inpatient',
    virtual: 'Virtual',
    home: 'Home',
    field: 'Field',
  }
  return types[type] || type
}

// Get badge color for status
const getStatusColor = (status: string) => {
  const colors: Record<string, string> = {
    planned: 'bg-blue-100 text-blue-800',
    'in-progress': 'bg-yellow-100 text-yellow-800',
    finished: 'bg-green-100 text-green-800',
    cancelled: 'bg-gray-100 text-gray-800',
  }
  return colors[status] || 'bg-gray-100 text-gray-800'
}

// Initialize edit form when entering edit mode
watch(isEditing, (editing) => {
  if (editing && store.currentPatient) {
    editForm.value = {
      given_name: store.currentPatient.given_name,
      family_name: store.currentPatient.family_name,
      birth_date: store.currentPatient.birth_date || undefined,
    }
    editErrors.value = {}
  }
})

// Validation
const validateName = (name: string | undefined, field: string): string | null => {
  if (!name?.trim()) return `${field} is required`
  if (name.length > 50) return `${field} must be at most 50 characters`
  return null
}

const validateBirthDate = (date: string | undefined | null): string | null => {
  if (!date) return null
  const parsed = new Date(date)
  if (isNaN(parsed.getTime())) return 'Invalid date format'
  if (parsed > new Date()) return 'Birth date cannot be in the future'
  if (parsed < new Date('1900-01-01')) return 'Birth date must be after 1900'
  return null
}

const validateEditField = (field: keyof PatientUpdate) => {
  switch (field) {
    case 'given_name':
      editErrors.value.given_name = validateName(editForm.value.given_name, 'Given name') || ''
      break
    case 'family_name':
      editErrors.value.family_name = validateName(editForm.value.family_name, 'Family name') || ''
      break
    case 'birth_date':
      editErrors.value.birth_date = validateBirthDate(editForm.value.birth_date) || ''
      break
  }
}

const isEditFormValid = computed(() => {
  const givenNameError = validateName(editForm.value.given_name, 'Given name')
  const familyNameError = validateName(editForm.value.family_name, 'Family name')
  const birthDateError = validateBirthDate(editForm.value.birth_date)
  return !givenNameError && !familyNameError && !birthDateError
})

const hasChanges = computed(() => {
  if (!store.currentPatient) return false
  return (
    editForm.value.given_name !== store.currentPatient.given_name ||
    editForm.value.family_name !== store.currentPatient.family_name ||
    (editForm.value.birth_date || null) !== store.currentPatient.birth_date
  )
})

const startEditing = () => {
  isEditing.value = true
}

const cancelEditing = () => {
  if (hasChanges.value) {
    if (!confirm('Discard unsaved changes?')) return
  }
  isEditing.value = false
}

const saveChanges = async () => {
  validateEditField('given_name')
  validateEditField('family_name')
  validateEditField('birth_date')

  if (!isEditFormValid.value || !hasChanges.value) return

  saving.value = true
  try {
    const patient = await store.updatePatient(patientId, editForm.value)
    if (patient) {
      isEditing.value = false
    }
  } finally {
    saving.value = false
  }
}

// Delete functionality
const canDelete = computed(() => {
  return deleteConfirmMrn.value === store.currentPatient?.mrn
})

const handleDelete = async () => {
  if (!canDelete.value) return

  deleting.value = true
  try {
    const success = await store.deletePatient(patientId)
    if (success) {
      showDeleteDialog.value = false
      router.push('/patients')
    }
  } finally {
    deleting.value = false
  }
}

const openDeleteDialog = () => {
  deleteConfirmMrn.value = ''
  showDeleteDialog.value = true
}
</script>

<template>
  <div class="space-y-6">
    <div class="flex items-center gap-4">
      <RouterLink
        to="/patients"
        class="text-sm text-muted-foreground hover:text-foreground"
      >
        ← Back to Patients
      </RouterLink>
    </div>

    <div
      v-if="store.loading"
      class="text-center py-8"
    >
      <p class="text-muted-foreground">
        Loading patient...
      </p>
    </div>

    <div
      v-else-if="store.error"
      class="rounded-lg border border-destructive p-4"
    >
      <p class="text-destructive">
        {{ store.error }}
      </p>
    </div>

    <div
      v-else-if="store.currentPatient"
      class="space-y-6"
    >
      <!-- Header with Edit button -->
      <div class="flex items-center justify-between">
        <div>
          <h1 class="text-3xl font-bold tracking-tight">
            {{ store.currentPatient.given_name }} {{ store.currentPatient.family_name }}
          </h1>
          <p class="text-muted-foreground">
            MRN: {{ store.currentPatient.mrn }}
          </p>
        </div>
        <div v-if="!isEditing" class="flex gap-2">
          <button
            class="inline-flex items-center justify-center rounded-md text-sm font-medium border border-input bg-background h-10 px-4 py-2 hover:bg-accent hover:text-accent-foreground"
            @click="startEditing"
          >
            <Pencil class="h-4 w-4 mr-2" />
            Edit
          </button>
        </div>
        <div v-else class="flex gap-2">
          <button
            class="inline-flex items-center justify-center rounded-md text-sm font-medium border border-input bg-background h-10 px-4 py-2 hover:bg-accent hover:text-accent-foreground"
            @click="cancelEditing"
          >
            Cancel
          </button>
          <button
            class="inline-flex items-center justify-center rounded-md text-sm font-medium bg-primary text-primary-foreground h-10 px-4 py-2 hover:bg-primary/90 disabled:opacity-50 disabled:pointer-events-none"
            :disabled="!hasChanges || !isEditFormValid || saving"
            @click="saveChanges"
          >
            <Loader2 v-if="saving" class="h-4 w-4 mr-2 animate-spin" />
            Save Changes
          </button>
        </div>
      </div>

      <div class="grid gap-6 md:grid-cols-2">
        <!-- Demographics Section -->
        <div class="rounded-lg border p-6">
          <h2 class="text-lg font-semibold mb-4">
            Demographics
          </h2>

          <!-- Read-only mode -->
          <dl v-if="!isEditing" class="space-y-3">
            <div>
              <dt class="text-sm text-muted-foreground">
                Given Name
              </dt>
              <dd>{{ store.currentPatient.given_name }}</dd>
            </div>
            <div>
              <dt class="text-sm text-muted-foreground">
                Family Name
              </dt>
              <dd>{{ store.currentPatient.family_name }}</dd>
            </div>
            <div>
              <dt class="text-sm text-muted-foreground">
                Birth Date
              </dt>
              <dd>{{ store.currentPatient.birth_date || 'Not recorded' }}</dd>
            </div>
          </dl>

          <!-- Edit mode -->
          <div v-else class="space-y-4">
            <div class="space-y-2">
              <label for="edit_given_name" class="text-sm font-medium">
                Given Name <span class="text-destructive">*</span>
              </label>
              <input
                id="edit_given_name"
                v-model="editForm.given_name"
                type="text"
                class="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                :class="{ 'border-destructive': editErrors.given_name }"
                @blur="validateEditField('given_name')"
              />
              <p v-if="editErrors.given_name" class="text-sm text-destructive">{{ editErrors.given_name }}</p>
            </div>

            <div class="space-y-2">
              <label for="edit_family_name" class="text-sm font-medium">
                Family Name <span class="text-destructive">*</span>
              </label>
              <input
                id="edit_family_name"
                v-model="editForm.family_name"
                type="text"
                class="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                :class="{ 'border-destructive': editErrors.family_name }"
                @blur="validateEditField('family_name')"
              />
              <p v-if="editErrors.family_name" class="text-sm text-destructive">{{ editErrors.family_name }}</p>
            </div>

            <div class="space-y-2">
              <label for="edit_birth_date" class="text-sm font-medium">
                Birth Date
              </label>
              <input
                id="edit_birth_date"
                v-model="editForm.birth_date"
                type="date"
                class="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                :class="{ 'border-destructive': editErrors.birth_date }"
                :max="new Date().toISOString().split('T')[0]"
                @blur="validateEditField('birth_date')"
              />
              <p v-if="editErrors.birth_date" class="text-sm text-destructive">{{ editErrors.birth_date }}</p>
            </div>
          </div>
        </div>

        <!-- System Info Section (always read-only) -->
        <div class="rounded-lg border p-6">
          <h2 class="text-lg font-semibold mb-4">
            System Info
          </h2>
          <dl class="space-y-3">
            <div>
              <dt class="text-sm text-muted-foreground">
                MRN
              </dt>
              <dd class="font-mono text-sm">
                {{ store.currentPatient.mrn }}
              </dd>
            </div>
            <div>
              <dt class="text-sm text-muted-foreground">
                Patient ID
              </dt>
              <dd class="font-mono text-sm">
                {{ store.currentPatient.id }}
              </dd>
            </div>
            <div>
              <dt class="text-sm text-muted-foreground">
                EHR ID
              </dt>
              <dd class="font-mono text-sm break-all">
                {{ store.currentPatient.ehr_id }}
              </dd>
            </div>
            <div>
              <dt class="text-sm text-muted-foreground">
                Created
              </dt>
              <dd>{{ new Date(store.currentPatient.created_at).toLocaleString() }}</dd>
            </div>
            <div>
              <dt class="text-sm text-muted-foreground">
                Updated
              </dt>
              <dd>{{ new Date(store.currentPatient.updated_at).toLocaleString() }}</dd>
            </div>
          </dl>
        </div>
      </div>

      <!-- Clinical Data -->
      <div class="grid gap-4 md:grid-cols-3">
        <!-- Recent Encounters -->
        <div class="rounded-lg border p-6">
          <div class="flex items-center justify-between mb-4">
            <h3 class="font-semibold">
              Recent Encounters
            </h3>
            <RouterLink
              to="/encounters"
              class="text-xs text-muted-foreground hover:text-foreground"
            >
              View all →
            </RouterLink>
          </div>

          <div v-if="encounterStore.loading" class="text-sm text-muted-foreground">
            Loading...
          </div>

          <div v-else-if="recentEncounters.length === 0" class="text-sm text-muted-foreground">
            No encounters yet
          </div>

          <div v-else class="space-y-3">
            <RouterLink
              v-for="encounter in recentEncounters"
              :key="encounter.id"
              :to="`/encounters/${encounter.id}`"
              class="block p-3 rounded-md hover:bg-accent transition-colors"
            >
              <div class="flex items-center justify-between mb-1">
                <span class="text-sm font-medium">{{ formatEncounterType(encounter.type) }}</span>
                <span
                  class="text-xs px-2 py-0.5 rounded-full"
                  :class="getStatusColor(encounter.status)"
                >
                  {{ encounter.status }}
                </span>
              </div>
              <div class="text-xs text-muted-foreground">
                {{ new Date(encounter.start_time).toLocaleDateString() }}
              </div>
            </RouterLink>
          </div>
        </div>

        <div class="rounded-lg border p-6 opacity-50">
          <h3 class="font-semibold">
            Vital Signs
          </h3>
          <p class="text-sm text-muted-foreground mt-1">
            Coming soon
          </p>
        </div>
        <div class="rounded-lg border p-6 opacity-50">
          <h3 class="font-semibold">
            Medications
          </h3>
          <p class="text-sm text-muted-foreground mt-1">
            Coming soon
          </p>
        </div>
      </div>

      <!-- Danger Zone -->
      <div class="rounded-lg border border-destructive/50 p-6">
        <div class="flex items-start gap-4">
          <AlertTriangle class="h-5 w-5 text-destructive mt-0.5" />
          <div class="flex-1">
            <h3 class="font-semibold text-destructive">Danger Zone</h3>
            <p class="text-sm text-muted-foreground mt-1">
              Deleting this patient is permanent and cannot be undone.
            </p>
            <button
              class="inline-flex items-center justify-center rounded-md text-sm font-medium bg-destructive text-destructive-foreground h-10 px-4 py-2 hover:bg-destructive/90 mt-4"
              @click="openDeleteDialog"
            >
              <Trash2 class="h-4 w-4 mr-2" />
              Delete Patient
            </button>
          </div>
        </div>
      </div>
    </div>

    <div
      v-else
      class="text-center py-8"
    >
      <p class="text-muted-foreground">
        Patient not found
      </p>
    </div>

    <!-- Delete Confirmation Dialog -->
    <DialogRoot :open="showDeleteDialog" @update:open="showDeleteDialog = $event">
      <DialogPortal>
        <DialogOverlay class="fixed inset-0 bg-black/50 data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0" />
        <DialogContent class="fixed left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 bg-background rounded-lg border shadow-lg w-full max-w-md p-6 data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0 data-[state=closed]:zoom-out-95 data-[state=open]:zoom-in-95">
          <div class="flex items-center justify-between mb-4">
            <DialogTitle class="text-lg font-semibold text-destructive">Delete Patient</DialogTitle>
            <DialogClose class="rounded-sm opacity-70 hover:opacity-100 focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2">
              <X class="h-4 w-4" />
              <span class="sr-only">Close</span>
            </DialogClose>
          </div>

          <DialogDescription class="text-sm text-muted-foreground mb-4">
            This action cannot be undone. The patient record will be permanently deleted.
          </DialogDescription>

          <div class="rounded-md bg-destructive/10 p-4 mb-4">
            <p class="text-sm">
              <strong>Warning:</strong> You are about to delete patient
              <span class="font-mono">{{ store.currentPatient?.mrn }}</span>.
            </p>
          </div>

          <div class="space-y-2 mb-6">
            <label for="delete_confirm_mrn" class="text-sm font-medium">
              Type the patient's MRN to confirm: <strong>{{ store.currentPatient?.mrn }}</strong>
            </label>
            <input
              id="delete_confirm_mrn"
              v-model="deleteConfirmMrn"
              type="text"
              placeholder="Enter MRN"
              class="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
            />
          </div>

          <!-- Error message -->
          <div v-if="store.error" class="rounded-md bg-destructive/10 p-3 text-sm text-destructive mb-4">
            {{ store.error }}
          </div>

          <div class="flex justify-end gap-3">
            <button
              type="button"
              class="inline-flex items-center justify-center rounded-md text-sm font-medium border border-input bg-background h-10 px-4 py-2 hover:bg-accent hover:text-accent-foreground"
              @click="showDeleteDialog = false"
            >
              Cancel
            </button>
            <button
              type="button"
              class="inline-flex items-center justify-center rounded-md text-sm font-medium bg-destructive text-destructive-foreground h-10 px-4 py-2 hover:bg-destructive/90 disabled:opacity-50 disabled:pointer-events-none"
              :disabled="!canDelete || deleting"
              @click="handleDelete"
            >
              <Loader2 v-if="deleting" class="h-4 w-4 mr-2 animate-spin" />
              Delete Patient
            </button>
          </div>
        </DialogContent>
      </DialogPortal>
    </DialogRoot>
  </div>
</template>
