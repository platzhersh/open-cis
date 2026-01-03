<script setup lang="ts">
import { onMounted, ref, computed, watch } from 'vue'
import { useRoute, useRouter, RouterLink } from 'vue-router'
import { DialogRoot, DialogPortal, DialogOverlay, DialogContent, DialogTitle, DialogDescription, DialogClose } from 'radix-vue'
import { X, Loader2, Pencil, Trash2, AlertTriangle } from 'lucide-vue-next'
import { useEncounterStore } from '@/stores/encounter'
import { usePatientStore } from '@/stores/patient'
import type { EncounterUpdate, EncounterType, EncounterStatus } from '@/types'

const route = useRoute()
const router = useRouter()
const encounterStore = useEncounterStore()
const patientStore = usePatientStore()

const encounterId = route.params.id as string

// Edit mode state
const isEditing = ref(false)
const editForm = ref<EncounterUpdate>({})
const editErrors = ref<Record<string, string>>({})
const saving = ref(false)

// Delete dialog state
const showDeleteDialog = ref(false)
const deleteConfirmId = ref('')
const deleting = ref(false)

// Encounter type and status options
const encounterTypes: { value: EncounterType; label: string }[] = [
  { value: 'ambulatory', label: 'Ambulatory' },
  { value: 'emergency', label: 'Emergency' },
  { value: 'inpatient', label: 'Inpatient' },
  { value: 'virtual', label: 'Virtual' },
  { value: 'home', label: 'Home' },
  { value: 'field', label: 'Field' },
]

const encounterStatuses: { value: EncounterStatus; label: string }[] = [
  { value: 'planned', label: 'Planned' },
  { value: 'in-progress', label: 'In Progress' },
  { value: 'finished', label: 'Finished' },
  { value: 'cancelled', label: 'Cancelled' },
]

onMounted(async () => {
  await encounterStore.fetchEncounter(encounterId)
  // Fetch patient details if we have the encounter
  if (encounterStore.currentEncounter) {
    await patientStore.fetchPatient(encounterStore.currentEncounter.patient_id)
  }
})

// Initialize edit form when entering edit mode
watch(isEditing, (editing) => {
  if (editing && encounterStore.currentEncounter) {
    editForm.value = {
      type: encounterStore.currentEncounter.type,
      status: encounterStore.currentEncounter.status,
      start_time: encounterStore.currentEncounter.start_time,
      end_time: encounterStore.currentEncounter.end_time,
      reason: encounterStore.currentEncounter.reason,
      provider_name: encounterStore.currentEncounter.provider_name,
      location: encounterStore.currentEncounter.location,
    }
    editErrors.value = {}
  }
})

// Validation
const validateStartTime = (startTime: string | undefined): string | null => {
  if (!startTime?.trim()) return 'Start time is required'
  const parsed = new Date(startTime)
  if (isNaN(parsed.getTime())) return 'Invalid date format'
  return null
}

const validateEndTime = (endTime: string | undefined | null, startTime: string | undefined): string | null => {
  if (!endTime) return null
  const parsedEnd = new Date(endTime)
  if (isNaN(parsedEnd.getTime())) return 'Invalid date format'

  if (startTime) {
    const parsedStart = new Date(startTime)
    if (!isNaN(parsedStart.getTime()) && parsedEnd <= parsedStart) {
      return 'End time must be after start time'
    }
  }
  return null
}

const validateStatus = (status: EncounterStatus | undefined, endTime: string | undefined | null): string | null => {
  if (status === 'finished' && !endTime) {
    return 'Finished encounters must have an end time'
  }
  return null
}

const validateEditField = (field: keyof EncounterUpdate) => {
  switch (field) {
    case 'start_time':
      editErrors.value.start_time = validateStartTime(editForm.value.start_time) || ''
      // Re-validate end_time when start_time changes
      if (editForm.value.end_time) {
        editErrors.value.end_time = validateEndTime(editForm.value.end_time, editForm.value.start_time) || ''
      }
      break
    case 'end_time':
      editErrors.value.end_time = validateEndTime(editForm.value.end_time, editForm.value.start_time) || ''
      // Re-validate status when end_time changes
      if (editForm.value.status) {
        editErrors.value.status = validateStatus(editForm.value.status, editForm.value.end_time) || ''
      }
      break
    case 'status':
      editErrors.value.status = validateStatus(editForm.value.status, editForm.value.end_time) || ''
      break
  }
}

const isEditFormValid = computed(() => {
  const startTimeError = validateStartTime(editForm.value.start_time)
  const endTimeError = validateEndTime(editForm.value.end_time, editForm.value.start_time)
  const statusError = validateStatus(editForm.value.status, editForm.value.end_time)
  return !startTimeError && !endTimeError && !statusError
})

const hasChanges = computed(() => {
  if (!encounterStore.currentEncounter) return false
  return (
    editForm.value.type !== encounterStore.currentEncounter.type ||
    editForm.value.status !== encounterStore.currentEncounter.status ||
    editForm.value.start_time !== encounterStore.currentEncounter.start_time ||
    (editForm.value.end_time || null) !== encounterStore.currentEncounter.end_time ||
    (editForm.value.reason || null) !== encounterStore.currentEncounter.reason ||
    (editForm.value.provider_name || null) !== encounterStore.currentEncounter.provider_name ||
    (editForm.value.location || null) !== encounterStore.currentEncounter.location
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
  validateEditField('start_time')
  validateEditField('end_time')
  validateEditField('status')

  if (!isEditFormValid.value || !hasChanges.value) return

  saving.value = true
  try {
    const encounter = await encounterStore.updateEncounter(encounterId, editForm.value)
    if (encounter) {
      isEditing.value = false
    }
  } finally {
    saving.value = false
  }
}

// Delete functionality
const canDelete = computed(() => {
  return deleteConfirmId.value === encounterStore.currentEncounter?.id
})

const handleDelete = async () => {
  if (!canDelete.value) return

  deleting.value = true
  try {
    const success = await encounterStore.deleteEncounter(encounterId)
    if (success) {
      showDeleteDialog.value = false
      // Navigate back to patient page if we have patient info, otherwise to encounters list
      if (encounterStore.currentEncounter?.patient_id) {
        router.push(`/patients/${encounterStore.currentEncounter.patient_id}`)
      } else {
        router.push('/encounters')
      }
    }
  } finally {
    deleting.value = false
  }
}

const openDeleteDialog = () => {
  deleteConfirmId.value = ''
  showDeleteDialog.value = true
}

// Utility functions
const formatDateTime = (dateStr: string | null): string => {
  if (!dateStr) return 'Not recorded'
  return new Date(dateStr).toLocaleString()
}

const formatDateTimeInput = (dateStr: string | null | undefined): string => {
  if (!dateStr) return ''
  // Convert ISO string to datetime-local format (YYYY-MM-DDTHH:mm)
  return dateStr.slice(0, 16)
}

const calculateDuration = (startTime: string, endTime: string | null): string => {
  if (!endTime) return 'Ongoing'
  const start = new Date(startTime)
  const end = new Date(endTime)
  const diffMs = end.getTime() - start.getTime()

  const hours = Math.floor(diffMs / (1000 * 60 * 60))
  const minutes = Math.floor((diffMs % (1000 * 60 * 60)) / (1000 * 60))

  if (hours > 0) {
    return `${hours}h ${minutes}m`
  }
  return `${minutes}m`
}

const getTypeBadgeClass = (type: EncounterType): string => {
  const baseClasses = 'inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold'
  const typeClasses: Record<EncounterType, string> = {
    ambulatory: 'bg-blue-100 text-blue-800',
    emergency: 'bg-red-100 text-red-800',
    inpatient: 'bg-purple-100 text-purple-800',
    virtual: 'bg-green-100 text-green-800',
    home: 'bg-yellow-100 text-yellow-800',
    field: 'bg-orange-100 text-orange-800',
  }
  return `${baseClasses} ${typeClasses[type]}`
}

const getStatusBadgeClass = (status: EncounterStatus): string => {
  const baseClasses = 'inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold'
  const statusClasses: Record<EncounterStatus, string> = {
    planned: 'bg-gray-100 text-gray-800',
    'in-progress': 'bg-blue-100 text-blue-800',
    finished: 'bg-green-100 text-green-800',
    cancelled: 'bg-red-100 text-red-800',
  }
  return `${baseClasses} ${statusClasses[status]}`
}

const getTypeLabel = (type: EncounterType): string => {
  return encounterTypes.find(t => t.value === type)?.label || type
}

const getStatusLabel = (status: EncounterStatus): string => {
  return encounterStatuses.find(s => s.value === status)?.label || status
}
</script>

<template>
  <div class="space-y-6">
    <div class="flex items-center gap-4">
      <RouterLink
        v-if="encounterStore.currentEncounter?.patient_id"
        :to="`/patients/${encounterStore.currentEncounter.patient_id}`"
        class="text-sm text-muted-foreground hover:text-foreground"
      >
        ← Back to Patient
      </RouterLink>
      <RouterLink
        v-else
        to="/encounters"
        class="text-sm text-muted-foreground hover:text-foreground"
      >
        ← Back to Encounters
      </RouterLink>
    </div>

    <div
      v-if="encounterStore.loading"
      class="text-center py-8"
    >
      <p class="text-muted-foreground">
        Loading encounter...
      </p>
    </div>

    <div
      v-else-if="encounterStore.error"
      class="rounded-lg border border-destructive p-4"
    >
      <p class="text-destructive">
        {{ encounterStore.error }}
      </p>
    </div>

    <div
      v-else-if="encounterStore.currentEncounter"
      class="space-y-6"
    >
      <!-- Header with Edit button -->
      <div class="flex items-center justify-between">
        <div>
          <div class="flex items-center gap-3 mb-2">
            <h1 class="text-3xl font-bold tracking-tight">
              {{ getTypeLabel(encounterStore.currentEncounter.type) }} Encounter
            </h1>
            <span :class="getTypeBadgeClass(encounterStore.currentEncounter.type)">
              {{ getTypeLabel(encounterStore.currentEncounter.type) }}
            </span>
            <span :class="getStatusBadgeClass(encounterStore.currentEncounter.status)">
              {{ getStatusLabel(encounterStore.currentEncounter.status) }}
            </span>
          </div>
          <p class="text-muted-foreground">
            {{ formatDateTime(encounterStore.currentEncounter.start_time) }}
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
        <!-- Encounter Details Section -->
        <div class="rounded-lg border p-6">
          <h2 class="text-lg font-semibold mb-4">
            Encounter Details
          </h2>

          <!-- Read-only mode -->
          <dl v-if="!isEditing" class="space-y-3">
            <div>
              <dt class="text-sm text-muted-foreground">
                Type
              </dt>
              <dd>
                <span :class="getTypeBadgeClass(encounterStore.currentEncounter.type)">
                  {{ getTypeLabel(encounterStore.currentEncounter.type) }}
                </span>
              </dd>
            </div>
            <div>
              <dt class="text-sm text-muted-foreground">
                Status
              </dt>
              <dd>
                <span :class="getStatusBadgeClass(encounterStore.currentEncounter.status)">
                  {{ getStatusLabel(encounterStore.currentEncounter.status) }}
                </span>
              </dd>
            </div>
            <div>
              <dt class="text-sm text-muted-foreground">
                Start Time
              </dt>
              <dd>{{ formatDateTime(encounterStore.currentEncounter.start_time) }}</dd>
            </div>
            <div>
              <dt class="text-sm text-muted-foreground">
                End Time
              </dt>
              <dd>{{ formatDateTime(encounterStore.currentEncounter.end_time) }}</dd>
            </div>
            <div v-if="encounterStore.currentEncounter.end_time">
              <dt class="text-sm text-muted-foreground">
                Duration
              </dt>
              <dd class="font-semibold">
                {{ calculateDuration(encounterStore.currentEncounter.start_time, encounterStore.currentEncounter.end_time) }}
              </dd>
            </div>
            <div>
              <dt class="text-sm text-muted-foreground">
                Reason
              </dt>
              <dd>{{ encounterStore.currentEncounter.reason || 'Not recorded' }}</dd>
            </div>
            <div>
              <dt class="text-sm text-muted-foreground">
                Provider
              </dt>
              <dd>{{ encounterStore.currentEncounter.provider_name || 'Not recorded' }}</dd>
            </div>
            <div>
              <dt class="text-sm text-muted-foreground">
                Location
              </dt>
              <dd>{{ encounterStore.currentEncounter.location || 'Not recorded' }}</dd>
            </div>
          </dl>

          <!-- Edit mode -->
          <div v-else class="space-y-4">
            <div class="space-y-2">
              <label for="edit_type" class="text-sm font-medium">
                Type <span class="text-destructive">*</span>
              </label>
              <select
                id="edit_type"
                v-model="editForm.type"
                class="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
              >
                <option v-for="type in encounterTypes" :key="type.value" :value="type.value">
                  {{ type.label }}
                </option>
              </select>
            </div>

            <div class="space-y-2">
              <label for="edit_status" class="text-sm font-medium">
                Status <span class="text-destructive">*</span>
              </label>
              <select
                id="edit_status"
                v-model="editForm.status"
                class="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                :class="{ 'border-destructive': editErrors.status }"
                @change="validateEditField('status')"
              >
                <option v-for="status in encounterStatuses" :key="status.value" :value="status.value">
                  {{ status.label }}
                </option>
              </select>
              <p v-if="editErrors.status" class="text-sm text-destructive">{{ editErrors.status }}</p>
            </div>

            <div class="space-y-2">
              <label for="edit_start_time" class="text-sm font-medium">
                Start Time <span class="text-destructive">*</span>
              </label>
              <input
                id="edit_start_time"
                v-model="editForm.start_time"
                type="datetime-local"
                class="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                :class="{ 'border-destructive': editErrors.start_time }"
                @blur="validateEditField('start_time')"
              />
              <p v-if="editErrors.start_time" class="text-sm text-destructive">{{ editErrors.start_time }}</p>
            </div>

            <div class="space-y-2">
              <label for="edit_end_time" class="text-sm font-medium">
                End Time
              </label>
              <input
                id="edit_end_time"
                v-model="editForm.end_time"
                type="datetime-local"
                class="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                :class="{ 'border-destructive': editErrors.end_time }"
                @blur="validateEditField('end_time')"
              />
              <p v-if="editErrors.end_time" class="text-sm text-destructive">{{ editErrors.end_time }}</p>
            </div>

            <div class="space-y-2">
              <label for="edit_reason" class="text-sm font-medium">
                Reason
              </label>
              <textarea
                id="edit_reason"
                v-model="editForm.reason"
                rows="3"
                class="flex w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                placeholder="Reason for encounter"
              />
            </div>

            <div class="space-y-2">
              <label for="edit_provider_name" class="text-sm font-medium">
                Provider Name
              </label>
              <input
                id="edit_provider_name"
                v-model="editForm.provider_name"
                type="text"
                class="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                placeholder="Provider name"
              />
            </div>

            <div class="space-y-2">
              <label for="edit_location" class="text-sm font-medium">
                Location
              </label>
              <input
                id="edit_location"
                v-model="editForm.location"
                type="text"
                class="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                placeholder="Location"
              />
            </div>
          </div>
        </div>

        <!-- Patient & System Info Section -->
        <div class="space-y-6">
          <!-- Patient Info (always read-only) -->
          <div class="rounded-lg border p-6">
            <h2 class="text-lg font-semibold mb-4">
              Patient
            </h2>
            <dl class="space-y-3">
              <div v-if="patientStore.currentPatient">
                <dt class="text-sm text-muted-foreground">
                  Name
                </dt>
                <dd>
                  <RouterLink
                    :to="`/patients/${patientStore.currentPatient.id}`"
                    class="text-primary hover:underline"
                  >
                    {{ patientStore.currentPatient.given_name }} {{ patientStore.currentPatient.family_name }}
                  </RouterLink>
                </dd>
              </div>
              <div v-if="patientStore.currentPatient">
                <dt class="text-sm text-muted-foreground">
                  MRN
                </dt>
                <dd class="font-mono text-sm">
                  {{ patientStore.currentPatient.mrn }}
                </dd>
              </div>
              <div v-else>
                <dt class="text-sm text-muted-foreground">
                  Patient ID
                </dt>
                <dd class="font-mono text-sm">
                  {{ encounterStore.currentEncounter.patient_id }}
                </dd>
              </div>
            </dl>
          </div>

          <!-- System Info Section (always read-only) -->
          <div class="rounded-lg border p-6">
            <h2 class="text-lg font-semibold mb-4">
              System Info
            </h2>
            <dl class="space-y-3">
              <div>
                <dt class="text-sm text-muted-foreground">
                  Encounter ID
                </dt>
                <dd class="font-mono text-sm break-all">
                  {{ encounterStore.currentEncounter.id }}
                </dd>
              </div>
              <div>
                <dt class="text-sm text-muted-foreground">
                  Created
                </dt>
                <dd>{{ new Date(encounterStore.currentEncounter.created_at).toLocaleString() }}</dd>
              </div>
              <div>
                <dt class="text-sm text-muted-foreground">
                  Updated
                </dt>
                <dd>{{ new Date(encounterStore.currentEncounter.updated_at).toLocaleString() }}</dd>
              </div>
            </dl>
          </div>
        </div>
      </div>

      <!-- Clinical Documentation Placeholders -->
      <div class="grid gap-4 md:grid-cols-3">
        <div class="rounded-lg border p-6 opacity-50">
          <h3 class="font-semibold">
            Observations
          </h3>
          <p class="text-sm text-muted-foreground mt-1">
            Vital signs, lab results - Coming soon
          </p>
        </div>
        <div class="rounded-lg border p-6 opacity-50">
          <h3 class="font-semibold">
            Diagnoses
          </h3>
          <p class="text-sm text-muted-foreground mt-1">
            ICD codes, conditions - Coming soon
          </p>
        </div>
        <div class="rounded-lg border p-6 opacity-50">
          <h3 class="font-semibold">
            Procedures
          </h3>
          <p class="text-sm text-muted-foreground mt-1">
            Clinical procedures - Coming soon
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
              Deleting this encounter is permanent and cannot be undone.
            </p>
            <button
              class="inline-flex items-center justify-center rounded-md text-sm font-medium bg-destructive text-destructive-foreground h-10 px-4 py-2 hover:bg-destructive/90 mt-4"
              @click="openDeleteDialog"
            >
              <Trash2 class="h-4 w-4 mr-2" />
              Delete Encounter
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
        Encounter not found
      </p>
    </div>

    <!-- Delete Confirmation Dialog -->
    <DialogRoot :open="showDeleteDialog" @update:open="showDeleteDialog = $event">
      <DialogPortal>
        <DialogOverlay class="fixed inset-0 bg-black/50 data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0" />
        <DialogContent class="fixed left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 bg-background rounded-lg border shadow-lg w-full max-w-md p-6 data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0 data-[state=closed]:zoom-out-95 data-[state=open]:zoom-in-95">
          <div class="flex items-center justify-between mb-4">
            <DialogTitle class="text-lg font-semibold text-destructive">Delete Encounter</DialogTitle>
            <DialogClose class="rounded-sm opacity-70 hover:opacity-100 focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2">
              <X class="h-4 w-4" />
              <span class="sr-only">Close</span>
            </DialogClose>
          </div>

          <DialogDescription class="text-sm text-muted-foreground mb-4">
            This action cannot be undone. The encounter record will be permanently deleted.
          </DialogDescription>

          <div class="rounded-md bg-destructive/10 p-4 mb-4">
            <p class="text-sm">
              <strong>Warning:</strong> You are about to delete encounter
              <span class="font-mono">{{ encounterStore.currentEncounter?.id }}</span>.
            </p>
          </div>

          <div class="space-y-2 mb-6">
            <label for="delete_confirm_id" class="text-sm font-medium">
              Type the encounter ID to confirm: <strong>{{ encounterStore.currentEncounter?.id }}</strong>
            </label>
            <input
              id="delete_confirm_id"
              v-model="deleteConfirmId"
              type="text"
              placeholder="Enter encounter ID"
              class="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
            />
          </div>

          <!-- Error message -->
          <div v-if="encounterStore.error" class="rounded-md bg-destructive/10 p-3 text-sm text-destructive mb-4">
            {{ encounterStore.error }}
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
              Delete Encounter
            </button>
          </div>
        </DialogContent>
      </DialogPortal>
    </DialogRoot>
  </div>
</template>
