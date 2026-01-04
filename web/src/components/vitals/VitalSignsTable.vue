<script setup lang="ts">
import { computed } from 'vue'
import type { VitalSignsReading } from '@/types'
import { getBPStatus, isInNormalRange } from '@/types/vitals'
import { Info } from 'lucide-vue-next'

const props = defineProps<{
  readings: VitalSignsReading[]
}>()

const emit = defineEmits<{
  showOpenEHR: [reading: VitalSignsReading]
}>()

// Sort by most recent first
const sortedReadings = computed(() => {
  return [...props.readings].sort(
    (a, b) => new Date(b.recorded_at).getTime() - new Date(a.recorded_at).getTime()
  )
})

function formatDate(dateStr: string): string {
  const date = new Date(dateStr)
  return date.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  })
}

function formatTime(dateStr: string): string {
  const date = new Date(dateStr)
  return date.toLocaleTimeString('en-US', {
    hour: 'numeric',
    minute: '2-digit',
  })
}

function formatBP(systolic: number | null, diastolic: number | null): string {
  if (systolic === null || diastolic === null) return '—'
  return `${systolic}/${diastolic}`
}

function getBPStatusClass(systolic: number | null, diastolic: number | null): string {
  if (systolic === null || diastolic === null) return ''
  const status = getBPStatus(systolic, diastolic)
  switch (status) {
    case 'high':
      return 'text-red-600 font-medium'
    case 'elevated':
      return 'text-yellow-600'
    default:
      return 'text-green-600'
  }
}

function getPulseStatusClass(pulseRate: number | null): string {
  if (pulseRate === null) return ''
  return isInNormalRange('pulse_rate', pulseRate) ? 'text-green-600' : 'text-yellow-600'
}
</script>

<template>
  <div class="rounded-lg border">
    <div class="overflow-x-auto">
      <table class="w-full text-sm">
        <thead>
          <tr class="border-b bg-muted/50">
            <th class="px-4 py-3 text-left font-medium">Date/Time</th>
            <th class="px-4 py-3 text-left font-medium">Blood Pressure</th>
            <th class="px-4 py-3 text-left font-medium">Pulse</th>
            <th class="px-4 py-3 text-right font-medium">Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="reading in sortedReadings"
            :key="reading.id"
            class="border-b last:border-0 hover:bg-muted/30 transition-colors"
          >
            <td class="px-4 py-3">
              <div class="font-medium">{{ formatDate(reading.recorded_at) }}</div>
              <div class="text-xs text-muted-foreground">{{ formatTime(reading.recorded_at) }}</div>
            </td>
            <td class="px-4 py-3">
              <span :class="getBPStatusClass(reading.systolic, reading.diastolic)">
                {{ formatBP(reading.systolic, reading.diastolic) }}
              </span>
              <span v-if="reading.systolic !== null" class="text-xs text-muted-foreground ml-1">mmHg</span>
            </td>
            <td class="px-4 py-3">
              <span v-if="reading.pulse_rate !== null" :class="getPulseStatusClass(reading.pulse_rate)">
                {{ reading.pulse_rate }}
              </span>
              <span v-else>—</span>
              <span v-if="reading.pulse_rate !== null" class="text-xs text-muted-foreground ml-1">bpm</span>
            </td>
            <td class="px-4 py-3 text-right">
              <button
                class="inline-flex items-center justify-center rounded-md text-sm font-medium h-8 px-2 gap-1 text-primary hover:bg-accent hover:text-accent-foreground"
                @click="emit('showOpenEHR', reading)"
              >
                <Info class="h-4 w-4" />
                <span class="hidden sm:inline">openEHR</span>
              </button>
            </td>
          </tr>
          <tr v-if="sortedReadings.length === 0">
            <td colspan="4" class="px-4 py-8 text-center text-muted-foreground">
              No vital signs recorded yet.
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>
