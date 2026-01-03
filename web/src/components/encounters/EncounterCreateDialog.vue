<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { DialogRoot, DialogPortal, DialogOverlay, DialogContent, DialogTitle, DialogDescription, DialogClose } from 'radix-vue'
import { X, Loader2, ChevronDown } from 'lucide-vue-next'
import { useEncounterStore } from '@/stores/encounter'
import { usePatientStore } from '@/stores/patient'
import type { EncounterCreate, EncounterType, EncounterStatus, Patient, Encounter } from '@/types'

const props = defineProps<{
  open: boolean
  patientId?: string
}>()

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'created', encounter: Encounter): void
}>()

const encounterStore = useEncounterStore()
const patientStore = usePatientStore()

const form = ref<EncounterCreate>({
  patient_id: '',
  type: 'ambulatory',
  status: 'planned',
  start_time: '',
  end_time: null,
  reason: null,
  provider_name: null,
  location: null,
})

const errors = ref<Record<string, string>>({})
const submitting = ref(false)
const patientSearchQuery = ref('')
const showPatientDropdown = ref(false)
const selectedPatient = ref<Patient | null>(null)

const encounterTypes: { value: EncounterType; label: string; description: string }[] = [
  { value: 'ambulatory', label: 'Ambulatory', description: 'Outpatient visit' },
  { value: 'emergency', label: 'Emergency', description: 'Emergency department' },
  { value: 'inpatient', label: 'Inpatient', description: 'Hospital admission' },
  { value: 'virtual', label: 'Virtual', description: 'Telemedicine visit' },
  { value: 'home', label: 'Home', description: 'Home health visit' },
  { value: 'field', label: 'Field', description: 'Field/mobile care' },
]

const encounterStatuses: { value: EncounterStatus; label: string; description: string }[] = [
  { value: 'planned', label: 'Planned', description: 'Scheduled for future' },
  { value: 'in-progress', label: 'In Progress', description: 'Currently ongoing' },
  { value: 'finished', label: 'Finished', description: 'Completed' },
  { value: 'cancelled', label: 'Cancelled', description: 'Cancelled' },
]

// Filter patients based on search query
const filteredPatients = computed(() => {
  if (!patientSearchQuery.value) return patientStore.patients

  const query = patientSearchQuery.value.toLowerCase()
  return patientStore.patients.filter(p =>
    p.given_name.toLowerCase().includes(query) ||
    p.family_name.toLowerCase().includes(query) ||
    p.mrn.toLowerCase().includes(query)
  )
})

// Reason character count
const reasonCharCount = computed(() => form.value.reason?.length || 0)
const reasonMaxLength = 500

// Validation functions
const validatePatient = (): string | null => {
  if (!form.value.patient_id) return 'Patient is required'
  return null
}

const validateType = (): string | null => {
  if (!form.value.type) return 'Encounter type is required'
  return null
}

const validateStatus = (): string | null => {
  if (!form.value.status) return 'Status is required'
  return null
}

const validateStartTime = (): string | null => {
  if (!form.value.start_time) return 'Start time is required'

  const startDate = new Date(form.value.start_time)
  if (isNaN(startDate.getTime())) return 'Invalid start time format'

  return null
}

const validateEndTime = (): string | null => {
  if (!form.value.end_time) return null // Optional field

  const endDate = new Date(form.value.end_time)
  if (isNaN(endDate.getTime())) return 'Invalid end time format'

  if (form.value.start_time) {
    const startDate = new Date(form.value.start_time)
    if (endDate <= startDate) return 'End time must be after start time'
  }

  return null
}

const validateReason = (): string | null => {
  if (form.value.reason && form.value.reason.length > reasonMaxLength) {
    return `Reason must be at most ${reasonMaxLength} characters`
  }
  return null
}

// Form validation
const isFormValid = computed(() => {
  const patientError = validatePatient()
  const typeError = validateType()
  const statusError = validateStatus()
  const startTimeError = validateStartTime()
  const endTimeError = validateEndTime()
  const reasonError = validateReason()

  // Finished status requires end time
  if (form.value.status === 'finished' && !form.value.end_time) {
    return false
  }

  return !patientError && !typeError && !statusError && !startTimeError && !endTimeError && !reasonError
})

// Watch for status changes to validate end time requirement
watch(() => form.value.status, (newStatus) => {
  if (newStatus === 'finished' && !form.value.end_time) {
    errors.value.end_time = 'End time is required for finished encounters'
  } else if (errors.value.end_time === 'End time is required for finished encounters') {
    delete errors.value.end_time
  }
})

// Watch for patientId prop changes
watch(() => props.patientId, (newPatientId) => {
  if (newPatientId) {
    form.value.patient_id = newPatientId
    const patient = patientStore.patients.find(p => p.id === newPatientId)
    if (patient) {
      selectedPatient.value = patient
      patientSearchQuery.value = `${patient.given_name} ${patient.family_name} (${patient.mrn})`
    }
  }
}, { immediate: true })

// Validate field
const validateField = (field: keyof EncounterCreate | 'all') => {
  if (field === 'all' || field === 'patient_id') {
    const error = validatePatient()
    if (error) errors.value.patient_id = error
    else delete errors.value.patient_id
  }

  if (field === 'all' || field === 'type') {
    const error = validateType()
    if (error) errors.value.type = error
    else delete errors.value.type
  }

  if (field === 'all' || field === 'status') {
    const error = validateStatus()
    if (error) errors.value.status = error
    else delete errors.value.status
  }

  if (field === 'all' || field === 'start_time') {
    const error = validateStartTime()
    if (error) errors.value.start_time = error
    else delete errors.value.start_time
  }

  if (field === 'all' || field === 'end_time') {
    const error = validateEndTime()
    if (error) errors.value.end_time = error
    else delete errors.value.end_time

    // Check finished status requirement
    if (form.value.status === 'finished' && !form.value.end_time) {
      errors.value.end_time = 'End time is required for finished encounters'
    }
  }

  if (field === 'all' || field === 'reason') {
    const error = validateReason()
    if (error) errors.value.reason = error
    else delete errors.value.reason
  }
}

// Handle patient selection
const selectPatient = (patient: Patient) => {
  selectedPatient.value = patient
  form.value.patient_id = patient.id
  patientSearchQuery.value = `${patient.given_name} ${patient.family_name} (${patient.mrn})`
  showPatientDropdown.value = false
  validateField('patient_id')
}

const handlePatientSearchBlur = () => {
  window.setTimeout(() => {
    showPatientDropdown.value = false
  }, 200)
}

// Handle form submission
const handleSubmit = async () => {
  validateField('all')

  if (!isFormValid.value) return

  submitting.value = true
  try {
    const encounter = await encounterStore.createEncounter(form.value)
    if (encounter) {
      emit('created', encounter)
      resetForm()
      emit('close')
    }
  } finally {
    submitting.value = false
  }
}

// Reset form
const resetForm = () => {
  form.value = {
    patient_id: '',
    type: 'ambulatory',
    status: 'planned',
    start_time: '',
    end_time: null,
    reason: null,
    provider_name: null,
    location: null,
  }
  errors.value = {}
  patientSearchQuery.value = ''
  selectedPatient.value = null
  showPatientDropdown.value = false

  // Re-apply patientId prop if present
  if (props.patientId) {
    form.value.patient_id = props.patientId
    const patient = patientStore.patients.find(p => p.id === props.patientId)
    if (patient) {
      selectedPatient.value = patient
      patientSearchQuery.value = `${patient.given_name} ${patient.family_name} (${patient.mrn})`
    }
  }
}

// Handle dialog close
const handleClose = () => {
  resetForm()
  emit('close')
}

// Load patients on mount if not already loaded
onMounted(() => {
  if (patientStore.patients.length === 0) {
    patientStore.fetchPatients()
  }
})
</script>

<template>
  <DialogRoot :open="props.open" @update:open="(open) => !open && handleClose()">
    <DialogPortal>
      <DialogOverlay class="fixed inset-0 bg-black/50 data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0 z-50" />
      <DialogContent class="fixed left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 bg-background rounded-lg border shadow-lg w-full max-w-2xl max-h-[90vh] overflow-y-auto p-6 data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0 data-[state=closed]:zoom-out-95 data-[state=open]:zoom-in-95 z-50">
        <div class="flex items-center justify-between mb-4">
          <DialogTitle class="text-lg font-semibold">Create New Encounter</DialogTitle>
          <DialogClose class="rounded-sm opacity-70 hover:opacity-100 focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2">
            <X class="h-4 w-4" />
            <span class="sr-only">Close</span>
          </DialogClose>
        </div>

        <DialogDescription class="text-sm text-muted-foreground mb-6">
          Record a new patient encounter. Required fields are marked with *.
        </DialogDescription>

        <form class="space-y-6" @submit.prevent="handleSubmit">
          <!-- Patient Selector -->
          <div class="space-y-2">
            <label for="patient" class="text-sm font-medium">
              Patient <span class="text-destructive">*</span>
            </label>
            <div class="relative">
              <div class="relative">
                <input
                  id="patient"
                  v-model="patientSearchQuery"
                  type="text"
                  placeholder="Search by name or MRN..."
                  class="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 pr-8 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                  :class="{ 'border-destructive': errors.patient_id }"
                  :disabled="!!props.patientId"
                  @focus="showPatientDropdown = true"
                  @blur="handlePatientSearchBlur"
                />
                <ChevronDown class="absolute right-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              </div>

              <!-- Patient Dropdown -->
              <div
                v-if="showPatientDropdown && !props.patientId"
                class="absolute z-10 w-full mt-1 bg-background border rounded-md shadow-lg max-h-60 overflow-auto"
              >
                <div
                  v-if="filteredPatients.length === 0"
                  class="px-3 py-2 text-sm text-muted-foreground"
                >
                  No patients found
                </div>
                <div
                  v-for="patient in filteredPatients"
                  :key="patient.id"
                  class="px-3 py-2 text-sm hover:bg-accent cursor-pointer"
                  @mousedown.prevent="selectPatient(patient)"
                >
                  <div class="font-medium">{{ patient.given_name }} {{ patient.family_name }}</div>
                  <div class="text-xs text-muted-foreground">MRN: {{ patient.mrn }}</div>
                </div>
              </div>
            </div>
            <p v-if="errors.patient_id" class="text-sm text-destructive">{{ errors.patient_id }}</p>
          </div>

          <!-- Type Selector (Radio Buttons) -->
          <div class="space-y-3">
            <label class="text-sm font-medium">
              Encounter Type <span class="text-destructive">*</span>
            </label>
            <div class="grid grid-cols-2 gap-3">
              <label
                v-for="type in encounterTypes"
                :key="type.value"
                class="relative flex items-start p-3 border rounded-md cursor-pointer hover:bg-accent"
                :class="{ 'border-primary bg-primary/5': form.type === type.value }"
              >
                <input
                  v-model="form.type"
                  type="radio"
                  :value="type.value"
                  class="sr-only"
                  @change="validateField('type')"
                />
                <div class="flex-1">
                  <div class="text-sm font-medium">{{ type.label }}</div>
                  <div class="text-xs text-muted-foreground">{{ type.description }}</div>
                </div>
                <div
                  class="flex-shrink-0 w-4 h-4 rounded-full border-2 ml-2"
                  :class="form.type === type.value ? 'border-primary bg-primary' : 'border-muted-foreground'"
                >
                  <div v-if="form.type === type.value" class="w-full h-full rounded-full bg-background scale-50"></div>
                </div>
              </label>
            </div>
            <p v-if="errors.type" class="text-sm text-destructive">{{ errors.type }}</p>
          </div>

          <!-- Status Selector (Radio Buttons) -->
          <div class="space-y-3">
            <label class="text-sm font-medium">
              Status <span class="text-destructive">*</span>
            </label>
            <div class="grid grid-cols-2 gap-3">
              <label
                v-for="status in encounterStatuses"
                :key="status.value"
                class="relative flex items-start p-3 border rounded-md cursor-pointer hover:bg-accent"
                :class="{ 'border-primary bg-primary/5': form.status === status.value }"
              >
                <input
                  v-model="form.status"
                  type="radio"
                  :value="status.value"
                  class="sr-only"
                  @change="validateField('status')"
                />
                <div class="flex-1">
                  <div class="text-sm font-medium">{{ status.label }}</div>
                  <div class="text-xs text-muted-foreground">{{ status.description }}</div>
                </div>
                <div
                  class="flex-shrink-0 w-4 h-4 rounded-full border-2 ml-2"
                  :class="form.status === status.value ? 'border-primary bg-primary' : 'border-muted-foreground'"
                >
                  <div v-if="form.status === status.value" class="w-full h-full rounded-full bg-background scale-50"></div>
                </div>
              </label>
            </div>
            <p v-if="errors.status" class="text-sm text-destructive">{{ errors.status }}</p>
          </div>

          <!-- Date & Time Fields -->
          <div class="grid grid-cols-2 gap-4">
            <!-- Start Time -->
            <div class="space-y-2">
              <label for="start_time" class="text-sm font-medium">
                Start Time <span class="text-destructive">*</span>
              </label>
              <input
                id="start_time"
                v-model="form.start_time"
                type="datetime-local"
                class="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                :class="{ 'border-destructive': errors.start_time }"
                @blur="validateField('start_time')"
              />
              <p v-if="errors.start_time" class="text-sm text-destructive">{{ errors.start_time }}</p>
            </div>

            <!-- End Time -->
            <div class="space-y-2">
              <label for="end_time" class="text-sm font-medium">
                End Time
                <span v-if="form.status === 'finished'" class="text-destructive">*</span>
              </label>
              <input
                id="end_time"
                v-model="form.end_time"
                type="datetime-local"
                class="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                :class="{ 'border-destructive': errors.end_time }"
                @blur="validateField('end_time')"
              />
              <p v-if="errors.end_time" class="text-sm text-destructive">{{ errors.end_time }}</p>
            </div>
          </div>

          <!-- Reason -->
          <div class="space-y-2">
            <label for="reason" class="text-sm font-medium flex justify-between">
              <span>Reason</span>
              <span class="text-xs text-muted-foreground">
                {{ reasonCharCount }} / {{ reasonMaxLength }}
              </span>
            </label>
            <textarea
              id="reason"
              v-model="form.reason"
              rows="3"
              :maxlength="reasonMaxLength"
              placeholder="Reason for encounter..."
              class="flex w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 resize-none"
              :class="{ 'border-destructive': errors.reason }"
              @blur="validateField('reason')"
            />
            <p v-if="errors.reason" class="text-sm text-destructive">{{ errors.reason }}</p>
          </div>

          <!-- Provider & Location -->
          <div class="grid grid-cols-2 gap-4">
            <!-- Provider Name -->
            <div class="space-y-2">
              <label for="provider_name" class="text-sm font-medium">Provider Name</label>
              <input
                id="provider_name"
                v-model="form.provider_name"
                type="text"
                placeholder="e.g., Dr. Smith"
                class="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
              />
            </div>

            <!-- Location -->
            <div class="space-y-2">
              <label for="location" class="text-sm font-medium">Location</label>
              <input
                id="location"
                v-model="form.location"
                type="text"
                placeholder="e.g., Room 302"
                class="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
              />
            </div>
          </div>

          <!-- Error Display -->
          <div v-if="encounterStore.error" class="rounded-md bg-destructive/10 p-3 text-sm text-destructive">
            {{ encounterStore.error }}
          </div>

          <!-- Actions -->
          <div class="flex justify-end gap-3 pt-4">
            <button
              type="button"
              class="inline-flex items-center justify-center rounded-md text-sm font-medium border border-input bg-background h-10 px-4 py-2 hover:bg-accent hover:text-accent-foreground"
              @click="handleClose"
            >
              Cancel
            </button>
            <button
              type="submit"
              class="inline-flex items-center justify-center rounded-md text-sm font-medium bg-primary text-primary-foreground h-10 px-4 py-2 hover:bg-primary/90 disabled:opacity-50 disabled:pointer-events-none"
              :disabled="!isFormValid || submitting"
            >
              <Loader2 v-if="submitting" class="h-4 w-4 mr-2 animate-spin" />
              Create Encounter
            </button>
          </div>
        </form>
      </DialogContent>
    </DialogPortal>
  </DialogRoot>
</template>
