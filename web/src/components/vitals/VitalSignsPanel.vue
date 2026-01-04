<script setup lang="ts">
import { ref, watch, onMounted } from 'vue'
import { SelectRoot, SelectTrigger, SelectValue, SelectPortal, SelectContent, SelectViewport, SelectItem, SelectItemText } from 'radix-vue'
import { useVitalsStore } from '@/stores/vitals'
import type { VitalSignsReading } from '@/types'
import VitalSignsChart from './VitalSignsChart.vue'
import VitalSignsTable from './VitalSignsTable.vue'
import RecordVitalsDialog from './RecordVitalsDialog.vue'
import OpenEHRMetadataPanel from '@/components/openehr/OpenEHRMetadataPanel.vue'
import { Plus, RefreshCw, ChevronDown } from 'lucide-vue-next'

const props = defineProps<{
  patientId: string
  patientName?: string
}>()

const store = useVitalsStore()

// UI State
const showRecordDialog = ref(false)
const showOpenEHRPanel = ref(false)
const selectedReading = ref<VitalSignsReading | null>(null)
const dateRange = ref('30')

// Load vitals when patient changes
watch(
  () => props.patientId,
  () => {
    loadVitals()
  },
  { immediate: true }
)

// Reload when date range changes
watch(dateRange, () => {
  loadVitals()
})

onMounted(() => {
  loadVitals()
})

async function loadVitals() {
  const days = parseInt(dateRange.value)
  const toDate = new Date()
  const fromDate = new Date()
  fromDate.setDate(fromDate.getDate() - days)

  await store.fetchVitals(props.patientId, {
    fromDate: fromDate.toISOString(),
    toDate: toDate.toISOString(),
  })
}

function handleReadingCreated() {
  showRecordDialog.value = false
}

function handleSelectReading(reading: VitalSignsReading) {
  selectedReading.value = reading
  showOpenEHRPanel.value = true
}

function handleShowOpenEHR(reading: VitalSignsReading) {
  selectedReading.value = reading
  showOpenEHRPanel.value = true
}

const dateRangeOptions = [
  { value: '7', label: 'Last 7 days' },
  { value: '30', label: 'Last 30 days' },
  { value: '90', label: 'Last 90 days' },
  { value: '365', label: 'Last year' },
]

const selectedRangeLabel = ref('Last 30 days')
watch(dateRange, (val) => {
  const opt = dateRangeOptions.find(o => o.value === val)
  selectedRangeLabel.value = opt?.label || 'Last 30 days'
})
</script>

<template>
  <div class="space-y-4">
    <!-- Header -->
    <div class="flex flex-wrap items-center justify-between gap-4">
      <div class="flex items-center gap-3">
        <h3 class="text-lg font-semibold">Vital Signs</h3>
        <span v-if="store.total > 0" class="text-sm text-muted-foreground">
          ({{ store.total }} readings)
        </span>
      </div>

      <div class="flex items-center gap-2">
        <!-- Date Range Selector -->
        <SelectRoot v-model="dateRange">
          <SelectTrigger
            class="inline-flex items-center justify-between rounded-md border border-input bg-background h-10 px-3 py-2 text-sm ring-offset-background focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 w-36"
          >
            <SelectValue :placeholder="selectedRangeLabel">{{ selectedRangeLabel }}</SelectValue>
            <ChevronDown class="h-4 w-4 opacity-50" />
          </SelectTrigger>
          <SelectPortal>
            <SelectContent
              class="min-w-[8rem] bg-background rounded-md border shadow-md overflow-hidden z-50"
              position="popper"
              :side-offset="5"
            >
              <SelectViewport class="p-1">
                <SelectItem
                  v-for="option in dateRangeOptions"
                  :key="option.value"
                  :value="option.value"
                  class="relative flex cursor-pointer select-none items-center rounded-sm py-1.5 px-2 text-sm outline-none hover:bg-accent hover:text-accent-foreground data-[highlighted]:bg-accent data-[highlighted]:text-accent-foreground"
                >
                  <SelectItemText>{{ option.label }}</SelectItemText>
                </SelectItem>
              </SelectViewport>
            </SelectContent>
          </SelectPortal>
        </SelectRoot>

        <!-- Refresh Button -->
        <button
          class="inline-flex items-center justify-center rounded-md border border-input bg-background h-10 w-10 hover:bg-accent hover:text-accent-foreground disabled:opacity-50"
          :disabled="store.loading"
          @click="loadVitals"
        >
          <RefreshCw :class="['h-4 w-4', { 'animate-spin': store.loading }]" />
        </button>

        <!-- Record Vitals Button -->
        <button
          class="inline-flex items-center justify-center rounded-md text-sm font-medium bg-primary text-primary-foreground h-10 px-4 hover:bg-primary/90"
          @click="showRecordDialog = true"
        >
          <Plus class="h-4 w-4 mr-2" />
          Record Vitals
        </button>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="store.loading && store.readings.length === 0" class="py-8 text-center text-muted-foreground">
      Loading vital signs...
    </div>

    <!-- Error State -->
    <div v-else-if="store.error" class="rounded-lg border border-destructive/50 bg-destructive/10 p-4 text-center text-destructive">
      {{ store.error }}
    </div>

    <!-- Content -->
    <template v-else>
      <!-- Chart -->
      <VitalSignsChart
        :readings="store.readings"
        @select-reading="handleSelectReading"
      />

      <!-- Table -->
      <div class="mt-6">
        <h4 class="font-medium mb-3">Recent Readings</h4>
        <VitalSignsTable
          :readings="store.readings"
          @show-open-e-h-r="handleShowOpenEHR"
        />
      </div>
    </template>

    <!-- Record Vitals Dialog -->
    <RecordVitalsDialog
      v-model:open="showRecordDialog"
      :patient-id="patientId"
      :patient-name="patientName"
      @created="handleReadingCreated"
    />

    <!-- openEHR Metadata Panel -->
    <OpenEHRMetadataPanel
      v-model:open="showOpenEHRPanel"
      :reading="selectedReading"
      :patient-id="patientId"
    />
  </div>
</template>
