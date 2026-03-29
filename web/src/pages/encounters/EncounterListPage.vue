<script setup lang="ts">
import { onMounted, ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { Plus, Loader2 } from 'lucide-vue-next'
import { useEncounterStore } from '@/stores/encounter'
import { usePatientStore } from '@/stores/patient'
import EncounterCreateDialog from '@/components/encounters/EncounterCreateDialog.vue'
import type { EncounterType, EncounterStatus } from '@/types'

const router = useRouter()
const encounterStore = useEncounterStore()
const patientStore = usePatientStore()
const showCreateDialog = ref(false)

onMounted(() => {
  encounterStore.fetchEncounters()
  patientStore.fetchPatients()
})

// Create a lookup map for patient names
const patientMap = computed(() => {
  const map = new Map<string, { given_name: string; family_name: string }>()
  patientStore.patients.forEach((patient) => {
    map.set(patient.id, {
      given_name: patient.given_name,
      family_name: patient.family_name,
    })
  })
  return map
})

const getPatientName = (patientId: string): string => {
  const patient = patientMap.value.get(patientId)
  if (!patient) return 'Unknown Patient'
  return `${patient.given_name} ${patient.family_name}`
}

const formatEncounterType = (type: EncounterType): string => {
  const typeMap: Record<EncounterType, string> = {
    ambulatory: 'Ambulatory',
    emergency: 'Emergency',
    inpatient: 'Inpatient',
    virtual: 'Virtual',
    home: 'Home',
    field: 'Field',
  }
  return typeMap[type] || type
}

const getTypeBadgeClass = (type: EncounterType): string => {
  const classMap: Record<EncounterType, string> = {
    ambulatory: 'bg-blue-100 text-blue-800 dark:bg-blue-950 dark:text-blue-200',
    emergency: 'bg-red-100 text-red-800 dark:bg-red-950 dark:text-red-200',
    inpatient: 'bg-purple-100 text-purple-800 dark:bg-purple-950 dark:text-purple-200',
    virtual: 'bg-green-100 text-green-800 dark:bg-green-950 dark:text-green-200',
    home: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-950 dark:text-yellow-200',
    field: 'bg-orange-100 text-orange-800 dark:bg-orange-950 dark:text-orange-200',
  }
  return classMap[type] || 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-200'
}

const formatEncounterStatus = (status: EncounterStatus): string => {
  const statusMap: Record<EncounterStatus, string> = {
    planned: 'Planned',
    'in-progress': 'In Progress',
    finished: 'Finished',
    cancelled: 'Cancelled',
  }
  return statusMap[status] || status
}

const getStatusBadgeClass = (status: EncounterStatus): string => {
  const classMap: Record<EncounterStatus, string> = {
    planned: 'bg-sky-100 text-sky-800 dark:bg-sky-950 dark:text-sky-200',
    'in-progress': 'bg-green-100 text-green-800 dark:bg-green-950 dark:text-green-200',
    finished: 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-200',
    cancelled: 'bg-red-100 text-red-800 dark:bg-red-950 dark:text-red-200',
  }
  return classMap[status] || 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-200'
}

const formatDateTime = (dateTimeString: string): string => {
  const date = new Date(dateTimeString)
  return new Intl.DateTimeFormat('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
    hour12: true,
  }).format(date)
}

const navigateToEncounter = (encounterId: string) => {
  router.push(`/encounters/${encounterId}`)
}

const navigateToPatient = (patientId: string, event: MouseEvent) => {
  event.stopPropagation()
  router.push(`/patients/${patientId}`)
}

const handleEncounterCreated = () => {
  showCreateDialog.value = false
  encounterStore.fetchEncounters()
}
</script>

<template>
  <div class="space-y-6">
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-3xl font-bold tracking-tight">
          Encounters
        </h1>
        <p class="text-muted-foreground">
          Manage patient encounters and visits
        </p>
      </div>
      <button
        class="inline-flex items-center justify-center rounded-md text-sm font-medium bg-primary text-primary-foreground h-10 px-4 py-2 hover:bg-primary/90"
        @click="showCreateDialog = true"
      >
        <Plus class="h-4 w-4 mr-2" />
        New Encounter
      </button>
    </div>

    <EncounterCreateDialog
      :open="showCreateDialog"
      @close="showCreateDialog = false"
      @created="handleEncounterCreated"
    />

    <div
      v-if="encounterStore.loading"
      class="text-center py-8"
    >
      <Loader2 class="h-5 w-5 animate-spin mx-auto mb-2 text-muted-foreground" />
      <p class="text-sm text-muted-foreground">
        Loading encounters...
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
      v-else-if="encounterStore.encounters.length === 0"
      class="text-center py-8"
    >
      <p class="text-muted-foreground">
        No encounters found
      </p>
      <p class="text-sm text-muted-foreground mt-1">
        Create your first encounter to get started
      </p>
    </div>

    <template v-else>
    <!-- Mobile: Card layout -->
    <div class="space-y-3 md:hidden">
      <div
        v-for="encounter in encounterStore.encounters"
        :key="encounter.id"
        class="rounded-lg border p-4 hover:bg-muted/50 cursor-pointer transition-colors"
        @click="navigateToEncounter(encounter.id)"
      >
        <div class="flex items-center justify-between mb-2">
          <button
            class="text-sm font-medium text-primary hover:underline text-left truncate"
            @click="navigateToPatient(encounter.patient_id, $event)"
          >
            {{ getPatientName(encounter.patient_id) }}
          </button>
          <div class="flex items-center gap-1.5 ml-2 shrink-0">
            <span
              class="inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium"
              :class="getTypeBadgeClass(encounter.type)"
            >
              {{ formatEncounterType(encounter.type) }}
            </span>
            <span
              class="inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium"
              :class="getStatusBadgeClass(encounter.status)"
            >
              {{ formatEncounterStatus(encounter.status) }}
            </span>
          </div>
        </div>
        <div class="flex items-center justify-between text-sm text-muted-foreground">
          <span>{{ formatDateTime(encounter.start_time) }}</span>
          <span v-if="encounter.provider_name">{{ encounter.provider_name }}</span>
        </div>
      </div>
    </div>

    <!-- Desktop: Table layout -->
    <div class="hidden md:block rounded-lg border">
      <div class="overflow-x-auto">
        <table class="w-full">
          <thead>
            <tr class="border-b bg-muted/50">
              <th class="h-12 px-4 text-left align-middle font-medium">
                Patient Name
              </th>
              <th class="h-12 px-4 text-left align-middle font-medium">
                Type
              </th>
              <th class="h-12 px-4 text-left align-middle font-medium">
                Status
              </th>
              <th class="h-12 px-4 text-left align-middle font-medium">
                Start Time
              </th>
              <th class="h-12 px-4 text-left align-middle font-medium">
                Provider
              </th>
              <th class="h-12 px-4 text-left align-middle font-medium">
                Location
              </th>
              <th class="h-12 px-4 text-left align-middle font-medium">
                Actions
              </th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="encounter in encounterStore.encounters"
              :key="encounter.id"
              class="border-b hover:bg-muted/50 cursor-pointer transition-colors"
              @click="navigateToEncounter(encounter.id)"
            >
              <td class="p-4 align-middle">
                <button
                  class="text-primary hover:underline text-left"
                  @click="navigateToPatient(encounter.patient_id, $event)"
                >
                  {{ getPatientName(encounter.patient_id) }}
                </button>
              </td>
              <td class="p-4 align-middle">
                <span
                  class="inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium"
                  :class="getTypeBadgeClass(encounter.type)"
                >
                  {{ formatEncounterType(encounter.type) }}
                </span>
              </td>
              <td class="p-4 align-middle">
                <span
                  class="inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium"
                  :class="getStatusBadgeClass(encounter.status)"
                >
                  {{ formatEncounterStatus(encounter.status) }}
                </span>
              </td>
              <td class="p-4 align-middle text-sm">
                {{ formatDateTime(encounter.start_time) }}
              </td>
              <td class="p-4 align-middle text-sm text-muted-foreground">
                {{ encounter.provider_name || '-' }}
              </td>
              <td class="p-4 align-middle text-sm text-muted-foreground">
                {{ encounter.location || '-' }}
              </td>
              <td class="p-4 align-middle">
                <button
                  class="text-sm text-primary hover:underline"
                  @click.stop="navigateToEncounter(encounter.id)"
                >
                  View
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
    </template>
  </div>
</template>
