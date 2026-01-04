<script setup lang="ts">
import { computed } from 'vue'
import { Line } from 'vue-chartjs'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  TimeScale,
  Filler,
  type ChartData,
  type ChartOptions,
} from 'chart.js'
import 'chartjs-adapter-date-fns'
import type { VitalSignsReading } from '@/types'
import { VITAL_SIGNS_NORMAL_RANGES } from '@/types/vitals'

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  TimeScale,
  Filler
)

const props = defineProps<{
  readings: VitalSignsReading[]
}>()

const emit = defineEmits<{
  selectReading: [reading: VitalSignsReading]
}>()

// Sort readings by date (oldest first for chart)
const sortedReadings = computed(() => {
  return [...props.readings].sort(
    (a, b) => new Date(a.recorded_at).getTime() - new Date(b.recorded_at).getTime()
  )
})

// Chart data for blood pressure
const bpChartData = computed<ChartData<'line'>>(() => {
  const labels = sortedReadings.value.map((r) => new Date(r.recorded_at))
  const systolicData = sortedReadings.value.map((r) => r.systolic)
  const diastolicData = sortedReadings.value.map((r) => r.diastolic)

  return {
    labels,
    datasets: [
      {
        label: 'Systolic',
        data: systolicData,
        borderColor: 'rgb(239, 68, 68)',
        backgroundColor: 'rgba(239, 68, 68, 0.1)',
        tension: 0.3,
        pointRadius: 4,
        pointHoverRadius: 6,
      },
      {
        label: 'Diastolic',
        data: diastolicData,
        borderColor: 'rgb(59, 130, 246)',
        backgroundColor: 'rgba(59, 130, 246, 0.1)',
        tension: 0.3,
        pointRadius: 4,
        pointHoverRadius: 6,
      },
    ],
  }
})

// Chart data for pulse
const pulseChartData = computed<ChartData<'line'>>(() => {
  const labels = sortedReadings.value.map((r) => new Date(r.recorded_at))
  const pulseData = sortedReadings.value.map((r) => r.pulse_rate)

  return {
    labels,
    datasets: [
      {
        label: 'Pulse Rate',
        data: pulseData,
        borderColor: 'rgb(34, 197, 94)',
        backgroundColor: 'rgba(34, 197, 94, 0.1)',
        tension: 0.3,
        fill: true,
        pointRadius: 4,
        pointHoverRadius: 6,
      },
    ],
  }
})

const bpChartOptions = computed<ChartOptions<'line'>>(() => ({
  responsive: true,
  maintainAspectRatio: false,
  interaction: {
    mode: 'index',
    intersect: false,
  },
  onClick: (_event, elements) => {
    if (elements.length > 0) {
      const index = elements[0].index
      emit('selectReading', sortedReadings.value[index])
    }
  },
  plugins: {
    legend: {
      position: 'top',
    },
    title: {
      display: true,
      text: 'Blood Pressure (mmHg)',
    },
    tooltip: {
      callbacks: {
        title: (items) => {
          if (items.length > 0 && items[0].parsed.x != null) {
            const date = new Date(items[0].parsed.x)
            return date.toLocaleDateString() + ' ' + date.toLocaleTimeString()
          }
          return ''
        },
      },
    },
  },
  scales: {
    x: {
      type: 'time',
      time: {
        unit: 'day',
        displayFormats: {
          day: 'MMM d',
        },
      },
      title: {
        display: true,
        text: 'Date',
      },
    },
    y: {
      min: 40,
      max: 200,
      title: {
        display: true,
        text: 'mmHg',
      },
      // Reference lines for normal ranges would need annotation plugin
    },
  },
}))

const pulseChartOptions = computed<ChartOptions<'line'>>(() => ({
  responsive: true,
  maintainAspectRatio: false,
  interaction: {
    mode: 'index',
    intersect: false,
  },
  onClick: (_event, elements) => {
    if (elements.length > 0) {
      const index = elements[0].index
      emit('selectReading', sortedReadings.value[index])
    }
  },
  plugins: {
    legend: {
      position: 'top',
    },
    title: {
      display: true,
      text: 'Pulse Rate (bpm)',
    },
    tooltip: {
      callbacks: {
        title: (items) => {
          if (items.length > 0 && items[0].parsed.x != null) {
            const date = new Date(items[0].parsed.x)
            return date.toLocaleDateString() + ' ' + date.toLocaleTimeString()
          }
          return ''
        },
      },
    },
  },
  scales: {
    x: {
      type: 'time',
      time: {
        unit: 'day',
        displayFormats: {
          day: 'MMM d',
        },
      },
      title: {
        display: true,
        text: 'Date',
      },
    },
    y: {
      min: 40,
      max: 140,
      title: {
        display: true,
        text: 'bpm',
      },
    },
  },
}))

// Check if we have BP data
const hasBPData = computed(() => sortedReadings.value.some((r) => r.systolic !== null))

// Check if we have pulse data
const hasPulseData = computed(() => sortedReadings.value.some((r) => r.pulse_rate !== null))

// Normal ranges for reference
const normalRanges = VITAL_SIGNS_NORMAL_RANGES
</script>

<template>
  <div class="space-y-6">
    <!-- Blood Pressure Chart -->
    <div v-if="hasBPData" class="rounded-lg border bg-card p-4">
      <div class="h-64">
        <Line :data="bpChartData" :options="bpChartOptions" />
      </div>
      <div class="mt-2 flex items-center justify-center gap-4 text-xs text-muted-foreground">
        <span>Normal: {{ normalRanges.systolic.min }}-{{ normalRanges.systolic.max }}/{{ normalRanges.diastolic.min }}-{{ normalRanges.diastolic.max }} mmHg</span>
      </div>
    </div>

    <!-- Pulse Chart -->
    <div v-if="hasPulseData" class="rounded-lg border bg-card p-4">
      <div class="h-48">
        <Line :data="pulseChartData" :options="pulseChartOptions" />
      </div>
      <div class="mt-2 flex items-center justify-center gap-4 text-xs text-muted-foreground">
        <span>Normal: {{ normalRanges.pulse_rate.min }}-{{ normalRanges.pulse_rate.max }} bpm</span>
      </div>
    </div>

    <!-- No data message -->
    <div v-if="!hasBPData && !hasPulseData" class="rounded-lg border bg-muted/50 p-8 text-center">
      <p class="text-muted-foreground">No vital signs recorded yet.</p>
      <p class="text-sm text-muted-foreground mt-1">Click "Record Vitals" to add the first reading.</p>
    </div>
  </div>
</template>
