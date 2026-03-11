<script setup lang="ts">
import { watch } from 'vue'
import { ShieldAlert, ShieldCheck, ShieldQuestion } from 'lucide-vue-next'
import { useCaveStore } from '@/stores/cave'
import { CAVE_CATEGORY_LABELS, CAVE_CRITICALITY_LABELS } from '@/types/cave'

const props = defineProps<{
  patientId: string
}>()

const emit = defineEmits<{
  manage: []
}>()

const store = useCaveStore()

watch(
  () => props.patientId,
  () => {
    store.fetchSummary(props.patientId)
  },
  { immediate: true }
)

function getCriticalityColor(criticality: string) {
  switch (criticality) {
    case 'high':
      return 'bg-red-100 text-red-800 border-red-200'
    case 'low':
      return 'bg-yellow-100 text-yellow-800 border-yellow-200'
    default:
      return 'bg-orange-100 text-orange-800 border-orange-200'
  }
}
</script>

<template>
  <div v-if="!store.loading || store.summary || store.error">
    <!-- Error state -->
    <div
      v-if="store.error && !store.summary"
      class="rounded-lg border-2 border-gray-200 bg-gray-50 p-4"
    >
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-2">
          <ShieldQuestion class="h-5 w-5 text-gray-500" />
          <span class="font-semibold text-sm text-gray-700">
            CAVE: Status Unavailable
          </span>
        </div>
        <button
          class="text-sm font-medium text-primary hover:underline"
          @click="emit('manage')"
        >
          Manage
        </button>
      </div>
    </div>

    <!-- Active allergies -->
    <div
      v-if="store.summary && store.summary.total_active > 0"
      :class="[
        'rounded-lg border-2 p-4',
        store.summary.has_high_criticality
          ? 'border-red-300 bg-red-50'
          : 'border-yellow-300 bg-yellow-50'
      ]"
    >
      <div class="flex items-center justify-between mb-3">
        <div class="flex items-center gap-2">
          <ShieldAlert
            :class="[
              'h-5 w-5',
              store.summary.has_high_criticality ? 'text-red-600' : 'text-yellow-600'
            ]"
          />
          <span class="font-semibold text-sm uppercase tracking-wide">
            CAVE
          </span>
          <span class="text-sm text-muted-foreground">
            ({{ store.summary.total_active }} active)
          </span>
        </div>
        <button
          class="text-sm font-medium text-primary hover:underline"
          @click="emit('manage')"
        >
          Manage
        </button>
      </div>

      <div class="flex flex-wrap gap-2">
        <div
          v-for="entry in store.summary.entries"
          :key="entry.id"
          :class="[
            'inline-flex flex-col rounded-md border px-3 py-1.5 text-xs',
            getCriticalityColor(entry.criticality)
          ]"
        >
          <span class="font-semibold">{{ entry.substance }}</span>
          <span class="opacity-75">
            {{ CAVE_CRITICALITY_LABELS[entry.criticality] }} &middot;
            {{ CAVE_CATEGORY_LABELS[entry.category] }}
          </span>
        </div>
      </div>
    </div>

    <!-- NKA declared -->
    <div
      v-else-if="store.summary && store.summary.has_nka_declaration"
      class="rounded-lg border-2 border-green-300 bg-green-50 p-4"
    >
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-2">
          <ShieldCheck class="h-5 w-5 text-green-600" />
          <span class="font-semibold text-sm text-green-800">
            CAVE: No Known Allergies
          </span>
        </div>
        <button
          class="text-sm font-medium text-primary hover:underline"
          @click="emit('manage')"
        >
          Manage
        </button>
      </div>
    </div>

    <!-- Not yet assessed -->
    <div
      v-else-if="store.summary"
      class="rounded-lg border-2 border-gray-200 bg-gray-50 p-4"
    >
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-2">
          <ShieldQuestion class="h-5 w-5 text-gray-500" />
          <div>
            <span class="font-semibold text-sm text-gray-700">
              CAVE: Not Yet Assessed
            </span>
            <span class="text-xs text-gray-500 ml-2">
              No allergy information has been recorded
            </span>
          </div>
        </div>
        <button
          class="text-sm font-medium text-primary hover:underline"
          @click="emit('manage')"
        >
          Record
        </button>
      </div>
    </div>
  </div>
</template>
