<script setup lang="ts">
import { onMounted, ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { Plus } from 'lucide-vue-next'
import { useEncounterStore } from '@/stores/encounter'
import { usePatientStore } from '@/stores/patient'
import type { Encounter, EncounterType, EncounterStatus } from '@/types'

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
    ambulatory: 'bg-blue-100 text-blue-800',
    emergency: 'bg-red-100 text-red-800',
    inpatient: 'bg-purple-100 text-purple-800',
    virtual: 'bg-green-100 text-green-800',
    home: 'bg-yellow-100 text-yellow-800',
    field: 'bg-orange-100 text-orange-800',
  }
  return classMap[type] || 'bg-gray-100 text-gray-800'
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
    planned: 'bg-sky-100 text-sky-800',
    'in-progress': 'bg-green-100 text-green-800',
    finished: 'bg-gray-100 text-gray-800',
    cancelled: 'bg-red-100 text-red-800',
  }
  return classMap[status] || 'bg-gray-100 text-gray-800'
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

const navigateToPatient = (patientId: string, event: Event) => {
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

    <!-- Note: Create dialog component will be implemented separately -->
    <!-- <EncounterCreateDialog
      v-model:open="showCreateDialog"
      @created="handleEncounterCreated"
    /> -->

    <div
      v-if="encounterStore.loading"
      class="text-center py-8"
    >
      <p class="text-muted-foreground">
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

    <div
      v-else
      class="rounded-lg border"
    >
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
