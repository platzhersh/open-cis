<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { DialogRoot, DialogPortal, DialogOverlay, DialogContent, DialogTitle, DialogDescription, DialogClose } from 'radix-vue'
import { X, Loader2 } from 'lucide-vue-next'
import { useVitalsStore } from '@/stores/vitals'
import type { VitalSignsReading } from '@/types'

const props = defineProps<{
  open: boolean
  patientId: string
  patientName?: string
}>()

const emit = defineEmits<{
  'update:open': [value: boolean]
  created: [reading: VitalSignsReading]
}>()

const store = useVitalsStore()

// Form state
const recordedAt = ref('')
const systolic = ref<number | undefined>(undefined)
const diastolic = ref<number | undefined>(undefined)
const pulseRate = ref<number | undefined>(undefined)

const submitting = ref(false)
const formError = ref<string | null>(null)

// Initialize date to now when dialog opens
watch(
  () => props.open,
  (isOpen) => {
    if (isOpen) {
      setNow()
      systolic.value = undefined
      diastolic.value = undefined
      pulseRate.value = undefined
      formError.value = null
    }
  }
)

function setNow() {
  const now = new Date()
  const pad = (n: number) => n.toString().padStart(2, '0')
  recordedAt.value = `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}T${pad(now.getHours())}:${pad(now.getMinutes())}`
}

// Validation
const hasAtLeastOneVital = computed(() => {
  return (systolic.value !== undefined && diastolic.value !== undefined) || pulseRate.value !== undefined
})

const bpIsComplete = computed(() => {
  const hasSys = systolic.value !== undefined && systolic.value !== null
  const hasDia = diastolic.value !== undefined && diastolic.value !== null
  return (hasSys && hasDia) || (!hasSys && !hasDia)
})

const canSubmit = computed(() => {
  return recordedAt.value && hasAtLeastOneVital.value && bpIsComplete.value && !submitting.value
})

async function handleSubmit() {
  if (!canSubmit.value) return

  formError.value = null
  submitting.value = true

  try {
    const reading = await store.recordVitals({
      patient_id: props.patientId,
      recorded_at: new Date(recordedAt.value).toISOString(),
      systolic: systolic.value ?? null,
      diastolic: diastolic.value ?? null,
      pulse_rate: pulseRate.value ?? null,
    })

    if (reading) {
      emit('created', reading)
      emit('update:open', false)
    } else {
      formError.value = store.error || 'Failed to record vital signs'
    }
  } catch (e) {
    formError.value = e instanceof Error ? e.message : 'Failed to record vital signs'
  } finally {
    submitting.value = false
  }
}

function handleOpenChange(open: boolean) {
  emit('update:open', open)
}
</script>

<template>
  <DialogRoot :open="open" @update:open="handleOpenChange">
    <DialogPortal>
      <DialogOverlay class="fixed inset-0 bg-black/50 data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0" />
      <DialogContent class="fixed left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 bg-background rounded-lg border shadow-lg w-full max-w-md p-6 data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0 data-[state=closed]:zoom-out-95 data-[state=open]:zoom-in-95">
        <div class="flex items-center justify-between mb-4">
          <DialogTitle class="text-lg font-semibold">Record Vital Signs</DialogTitle>
          <DialogClose class="rounded-sm opacity-70 hover:opacity-100 focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2">
            <X class="h-4 w-4" />
            <span class="sr-only">Close</span>
          </DialogClose>
        </div>

        <DialogDescription class="text-sm text-muted-foreground mb-4">
          Record vital signs for {{ patientName || 'this patient' }}.
        </DialogDescription>

        <form class="space-y-4" @submit.prevent="handleSubmit">
          <!-- Date/Time -->
          <div class="space-y-2">
            <label for="recorded-at" class="text-sm font-medium">
              Date & Time <span class="text-destructive">*</span>
            </label>
            <div class="flex gap-2">
              <input
                id="recorded-at"
                v-model="recordedAt"
                type="datetime-local"
                required
                class="flex h-10 flex-1 rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
              />
              <button
                type="button"
                class="inline-flex items-center justify-center rounded-md text-sm font-medium border border-input bg-background h-10 px-3 hover:bg-accent hover:text-accent-foreground"
                @click="setNow"
              >
                Now
              </button>
            </div>
          </div>

          <!-- Blood Pressure Section -->
          <div class="space-y-2">
            <label class="text-sm font-medium">Blood Pressure</label>
            <div class="grid grid-cols-2 gap-4">
              <div class="space-y-1">
                <label for="systolic" class="text-xs text-muted-foreground">Systolic</label>
                <div class="flex items-center gap-2">
                  <input
                    id="systolic"
                    v-model.number="systolic"
                    type="number"
                    min="50"
                    max="300"
                    placeholder="120"
                    class="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                  />
                  <span class="text-sm text-muted-foreground">mmHg</span>
                </div>
              </div>
              <div class="space-y-1">
                <label for="diastolic" class="text-xs text-muted-foreground">Diastolic</label>
                <div class="flex items-center gap-2">
                  <input
                    id="diastolic"
                    v-model.number="diastolic"
                    type="number"
                    min="30"
                    max="200"
                    placeholder="80"
                    class="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                  />
                  <span class="text-sm text-muted-foreground">mmHg</span>
                </div>
              </div>
            </div>
            <p v-if="!bpIsComplete" class="text-sm text-destructive">
              Both systolic and diastolic must be provided together.
            </p>
          </div>

          <!-- Pulse Section -->
          <div class="space-y-2">
            <label class="text-sm font-medium">Pulse</label>
            <div class="space-y-1">
              <label for="pulse-rate" class="text-xs text-muted-foreground">Heart Rate</label>
              <div class="flex items-center gap-2">
                <input
                  id="pulse-rate"
                  v-model.number="pulseRate"
                  type="number"
                  min="20"
                  max="300"
                  placeholder="72"
                  class="flex h-10 w-32 rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                />
                <span class="text-sm text-muted-foreground">bpm</span>
              </div>
            </div>
          </div>

          <!-- Validation message -->
          <p v-if="!hasAtLeastOneVital" class="text-sm text-muted-foreground">
            Enter at least blood pressure or pulse rate.
          </p>

          <!-- Error message -->
          <div v-if="formError" class="rounded-md bg-destructive/10 p-3 text-sm text-destructive">
            {{ formError }}
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
              :disabled="!canSubmit"
            >
              <Loader2 v-if="submitting" class="h-4 w-4 mr-2 animate-spin" />
              Record Vital Signs
            </button>
          </div>
        </form>
      </DialogContent>
    </DialogPortal>
  </DialogRoot>
</template>
