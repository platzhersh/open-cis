<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'
import { Loader2 } from 'lucide-vue-next'
import { usePatientStore } from '@/stores/patient'
import PatientCreateDialog from '@/components/patients/PatientCreateDialog.vue'

const store = usePatientStore()
const showCreateDialog = ref(false)

onMounted(() => {
  store.fetchPatients()
})

const handlePatientCreated = () => {
  showCreateDialog.value = false
  store.fetchPatients()
}
</script>

<template>
  <div class="space-y-6">
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-3xl font-bold tracking-tight">
          Patients
        </h1>
        <p class="text-muted-foreground">
          Manage patient records and demographics
        </p>
      </div>
      <button
        class="inline-flex items-center justify-center rounded-md text-sm font-medium bg-primary text-primary-foreground h-10 px-4 py-2 hover:bg-primary/90"
        @click="showCreateDialog = true"
      >
        Add Patient
      </button>
    </div>

    <PatientCreateDialog
      v-model:open="showCreateDialog"
      @created="handlePatientCreated"
    />

    <div
      v-if="store.loading"
      class="text-center py-8"
    >
      <Loader2 class="h-5 w-5 animate-spin mx-auto mb-2 text-muted-foreground" />
      <p class="text-sm text-muted-foreground">
        Loading patients...
      </p>
    </div>

    <div
      v-else-if="store.error"
      class="rounded-lg border border-destructive p-4"
    >
      <p class="text-destructive">
        {{ store.error }}
      </p>
    </div>

    <div
      v-else-if="store.patients.length === 0"
      class="text-center py-8"
    >
      <p class="text-muted-foreground">
        No patients found
      </p>
      <p class="text-sm text-muted-foreground mt-1">
        Add your first patient to get started
      </p>
    </div>

    <template v-else>
    <!-- Mobile: Card layout -->
    <div class="space-y-3 md:hidden">
      <RouterLink
        v-for="patient in store.patients"
        :key="patient.id"
        :to="`/patients/${patient.id}`"
        class="block rounded-lg border p-4 hover:bg-muted/50 transition-colors"
      >
        <div class="flex items-center justify-between">
          <div class="min-w-0">
            <p class="font-medium truncate">
              {{ patient.given_name }} {{ patient.family_name }}
            </p>
            <p class="text-sm text-muted-foreground font-mono mt-0.5">
              {{ patient.mrn }}
            </p>
          </div>
          <div class="text-sm text-muted-foreground ml-4 shrink-0">
            {{ patient.birth_date || '-' }}
          </div>
        </div>
      </RouterLink>
    </div>

    <!-- Desktop: Table layout -->
    <div class="hidden md:block rounded-lg border">
      <div class="overflow-x-auto">
        <table class="w-full">
          <thead>
            <tr class="border-b bg-muted/50">
              <th class="h-12 px-4 text-left align-middle font-medium">
                MRN
              </th>
              <th class="h-12 px-4 text-left align-middle font-medium">
                Name
              </th>
              <th class="h-12 px-4 text-left align-middle font-medium">
                Birth Date
              </th>
              <th class="h-12 px-4 text-left align-middle font-medium">
                Actions
              </th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="patient in store.patients"
              :key="patient.id"
              class="border-b hover:bg-muted/50 transition-colors"
            >
              <td class="p-4 align-middle font-mono text-sm">
                {{ patient.mrn }}
              </td>
              <td class="p-4 align-middle">
                {{ patient.given_name }} {{ patient.family_name }}
              </td>
              <td class="p-4 align-middle text-muted-foreground">
                {{ patient.birth_date || '-' }}
              </td>
              <td class="p-4 align-middle">
                <RouterLink
                  :to="`/patients/${patient.id}`"
                  class="text-sm text-primary hover:underline"
                >
                  View
                </RouterLink>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
    </template>
  </div>
</template>
