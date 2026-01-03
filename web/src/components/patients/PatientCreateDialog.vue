<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useDebounceFn } from '@vueuse/core'
import { DialogRoot, DialogPortal, DialogOverlay, DialogContent, DialogTitle, DialogDescription, DialogClose } from 'radix-vue'
import { X, Loader2, Check, AlertCircle } from 'lucide-vue-next'
import { usePatientStore } from '@/stores/patient'
import type { PatientCreate } from '@/types'

const props = defineProps<{
  open: boolean
}>()

const emit = defineEmits<{
  (e: 'update:open', value: boolean): void
  (e: 'created'): void
}>()

const store = usePatientStore()

const form = ref<PatientCreate>({
  mrn: '',
  given_name: '',
  family_name: '',
  birth_date: undefined,
})

const errors = ref<Record<string, string>>({})
const mrnStatus = ref<'idle' | 'checking' | 'available' | 'taken'>('idle')
const submitting = ref(false)

// MRN validation regex: 3-20 alphanumeric characters and hyphens
const mrnRegex = /^[A-Za-z0-9-]{3,20}$/

const validateMrn = (mrn: string): string | null => {
  if (!mrn) return 'MRN is required'
  if (mrn.length < 3) return 'MRN must be at least 3 characters'
  if (mrn.length > 20) return 'MRN must be at most 20 characters'
  if (!mrnRegex.test(mrn)) return 'MRN must contain only letters, numbers, and hyphens'
  return null
}

const validateName = (name: string, field: string): string | null => {
  if (!name.trim()) return `${field} is required`
  if (name.length > 50) return `${field} must be at most 50 characters`
  return null
}

const validateBirthDate = (date: string | undefined): string | null => {
  if (!date) return null // Optional field
  const parsed = new Date(date)
  if (isNaN(parsed.getTime())) return 'Invalid date format'
  if (parsed > new Date()) return 'Birth date cannot be in the future'
  if (parsed < new Date('1900-01-01')) return 'Birth date must be after 1900'
  return null
}

// Debounced MRN uniqueness check
const checkMrnExists = useDebounceFn(async (mrn: string) => {
  const mrnError = validateMrn(mrn)
  if (mrnError) {
    mrnStatus.value = 'idle'
    return
  }

  mrnStatus.value = 'checking'
  const exists = await store.checkMrnExists(mrn)
  mrnStatus.value = exists ? 'taken' : 'available'
}, 500)

watch(() => form.value.mrn, (newMrn) => {
  errors.value.mrn = validateMrn(newMrn) || ''
  if (!errors.value.mrn) {
    checkMrnExists(newMrn)
  } else {
    mrnStatus.value = 'idle'
  }
})

const isFormValid = computed(() => {
  const mrnError = validateMrn(form.value.mrn)
  const givenNameError = validateName(form.value.given_name, 'Given name')
  const familyNameError = validateName(form.value.family_name, 'Family name')
  const birthDateError = validateBirthDate(form.value.birth_date)

  return !mrnError && !givenNameError && !familyNameError && !birthDateError && mrnStatus.value === 'available'
})

const validateField = (field: keyof PatientCreate) => {
  switch (field) {
    case 'mrn':
      errors.value.mrn = validateMrn(form.value.mrn) || ''
      break
    case 'given_name':
      errors.value.given_name = validateName(form.value.given_name, 'Given name') || ''
      break
    case 'family_name':
      errors.value.family_name = validateName(form.value.family_name, 'Family name') || ''
      break
    case 'birth_date':
      errors.value.birth_date = validateBirthDate(form.value.birth_date) || ''
      break
  }
}

const handleSubmit = async () => {
  // Validate all fields
  validateField('mrn')
  validateField('given_name')
  validateField('family_name')
  validateField('birth_date')

  if (!isFormValid.value) return

  submitting.value = true
  try {
    const patient = await store.createPatient(form.value)
    if (patient) {
      emit('created')
      resetForm()
    }
  } finally {
    submitting.value = false
  }
}

const resetForm = () => {
  form.value = {
    mrn: '',
    given_name: '',
    family_name: '',
    birth_date: undefined,
  }
  errors.value = {}
  mrnStatus.value = 'idle'
}

const handleOpenChange = (open: boolean) => {
  emit('update:open', open)
  if (!open) {
    resetForm()
  }
}
</script>

<template>
  <DialogRoot :open="props.open" @update:open="handleOpenChange">
    <DialogPortal>
      <DialogOverlay class="fixed inset-0 bg-black/50 data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0" />
      <DialogContent class="fixed left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 bg-background rounded-lg border shadow-lg w-full max-w-md p-6 data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0 data-[state=closed]:zoom-out-95 data-[state=open]:zoom-in-95">
        <div class="flex items-center justify-between mb-4">
          <DialogTitle class="text-lg font-semibold">Add New Patient</DialogTitle>
          <DialogClose class="rounded-sm opacity-70 hover:opacity-100 focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2">
            <X class="h-4 w-4" />
            <span class="sr-only">Close</span>
          </DialogClose>
        </div>

        <DialogDescription class="text-sm text-muted-foreground mb-4">
          Create a new patient record. Required fields are marked with *.
        </DialogDescription>

        <form class="space-y-4" @submit.prevent="handleSubmit">
          <!-- MRN Field -->
          <div class="space-y-2">
            <label for="mrn" class="text-sm font-medium">
              MRN <span class="text-destructive">*</span>
            </label>
            <div class="relative">
              <input
                id="mrn"
                v-model="form.mrn"
                type="text"
                placeholder="e.g., MRN-12345"
                class="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                :class="{ 'border-destructive': errors.mrn || mrnStatus === 'taken' }"
                @blur="validateField('mrn')"
              />
              <div class="absolute right-3 top-1/2 -translate-y-1/2">
                <Loader2 v-if="mrnStatus === 'checking'" class="h-4 w-4 animate-spin text-muted-foreground" />
                <Check v-else-if="mrnStatus === 'available'" class="h-4 w-4 text-green-600" />
                <AlertCircle v-else-if="mrnStatus === 'taken'" class="h-4 w-4 text-destructive" />
              </div>
            </div>
            <p v-if="errors.mrn" class="text-sm text-destructive">{{ errors.mrn }}</p>
            <p v-else-if="mrnStatus === 'taken'" class="text-sm text-destructive">MRN already exists</p>
            <p v-else-if="mrnStatus === 'available'" class="text-sm text-green-600">MRN is available</p>
          </div>

          <!-- Given Name Field -->
          <div class="space-y-2">
            <label for="given_name" class="text-sm font-medium">
              Given Name <span class="text-destructive">*</span>
            </label>
            <input
              id="given_name"
              v-model="form.given_name"
              type="text"
              placeholder="First name"
              class="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
              :class="{ 'border-destructive': errors.given_name }"
              @blur="validateField('given_name')"
            />
            <p v-if="errors.given_name" class="text-sm text-destructive">{{ errors.given_name }}</p>
          </div>

          <!-- Family Name Field -->
          <div class="space-y-2">
            <label for="family_name" class="text-sm font-medium">
              Family Name <span class="text-destructive">*</span>
            </label>
            <input
              id="family_name"
              v-model="form.family_name"
              type="text"
              placeholder="Last name"
              class="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
              :class="{ 'border-destructive': errors.family_name }"
              @blur="validateField('family_name')"
            />
            <p v-if="errors.family_name" class="text-sm text-destructive">{{ errors.family_name }}</p>
          </div>

          <!-- Birth Date Field -->
          <div class="space-y-2">
            <label for="birth_date" class="text-sm font-medium">
              Birth Date
            </label>
            <input
              id="birth_date"
              v-model="form.birth_date"
              type="date"
              class="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
              :class="{ 'border-destructive': errors.birth_date }"
              :max="new Date().toISOString().split('T')[0]"
              @blur="validateField('birth_date')"
            />
            <p v-if="errors.birth_date" class="text-sm text-destructive">{{ errors.birth_date }}</p>
          </div>

          <!-- Error message -->
          <div v-if="store.error" class="rounded-md bg-destructive/10 p-3 text-sm text-destructive">
            {{ store.error }}
          </div>

          <!-- Actions -->
          <div class="flex justify-end gap-3 pt-4">
            <button
              type="button"
              class="inline-flex items-center justify-center rounded-md text-sm font-medium border border-input bg-background h-10 px-4 py-2 hover:bg-accent hover:text-accent-foreground"
              @click="handleOpenChange(false)"
            >
              Cancel
            </button>
            <button
              type="submit"
              class="inline-flex items-center justify-center rounded-md text-sm font-medium bg-primary text-primary-foreground h-10 px-4 py-2 hover:bg-primary/90 disabled:opacity-50 disabled:pointer-events-none"
              :disabled="!isFormValid || submitting"
            >
              <Loader2 v-if="submitting" class="h-4 w-4 mr-2 animate-spin" />
              Create Patient
            </button>
          </div>
        </form>
      </DialogContent>
    </DialogPortal>
  </DialogRoot>
</template>
