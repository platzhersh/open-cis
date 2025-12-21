<script setup lang="ts">
import { onMounted } from 'vue'
import { RouterLink } from 'vue-router'
import { usePatientStore } from '@/stores/patient'

const store = usePatientStore()

onMounted(() => {
  store.fetchPatients()
})
</script>

<template>
  <div class="space-y-6">
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-3xl font-bold tracking-tight">Patients</h1>
        <p class="text-muted-foreground">
          Manage patient records and demographics
        </p>
      </div>
      <button
        class="inline-flex items-center justify-center rounded-md text-sm font-medium bg-primary text-primary-foreground h-10 px-4 py-2 hover:bg-primary/90"
      >
        Add Patient
      </button>
    </div>

    <div v-if="store.loading" class="text-center py-8">
      <p class="text-muted-foreground">Loading patients...</p>
    </div>

    <div v-else-if="store.error" class="rounded-lg border border-destructive p-4">
      <p class="text-destructive">{{ store.error }}</p>
    </div>

    <div v-else-if="store.patients.length === 0" class="text-center py-8">
      <p class="text-muted-foreground">No patients found</p>
      <p class="text-sm text-muted-foreground mt-1">
        Add your first patient to get started
      </p>
    </div>

    <div v-else class="rounded-lg border">
      <table class="w-full">
        <thead>
          <tr class="border-b bg-muted/50">
            <th class="h-12 px-4 text-left align-middle font-medium">MRN</th>
            <th class="h-12 px-4 text-left align-middle font-medium">Name</th>
            <th class="h-12 px-4 text-left align-middle font-medium">Birth Date</th>
            <th class="h-12 px-4 text-left align-middle font-medium">Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="patient in store.patients"
            :key="patient.id"
            class="border-b"
          >
            <td class="p-4 align-middle font-mono text-sm">{{ patient.mrn }}</td>
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
