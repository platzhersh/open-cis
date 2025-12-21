<script setup lang="ts">
import { onMounted } from 'vue'
import { useRoute, RouterLink } from 'vue-router'
import { usePatientStore } from '@/stores/patient'

const route = useRoute()
const store = usePatientStore()

const patientId = route.params.id as string

onMounted(() => {
  store.fetchPatient(patientId)
})
</script>

<template>
  <div class="space-y-6">
    <div class="flex items-center gap-4">
      <RouterLink
        to="/patients"
        class="text-sm text-muted-foreground hover:text-foreground"
      >
        ← Back to Patients
      </RouterLink>
    </div>

    <div v-if="store.loading" class="text-center py-8">
      <p class="text-muted-foreground">Loading patient...</p>
    </div>

    <div v-else-if="store.error" class="rounded-lg border border-destructive p-4">
      <p class="text-destructive">{{ store.error }}</p>
    </div>

    <div v-else-if="store.currentPatient" class="space-y-6">
      <div>
        <h1 class="text-3xl font-bold tracking-tight">
          {{ store.currentPatient.given_name }} {{ store.currentPatient.family_name }}
        </h1>
        <p class="text-muted-foreground">
          MRN: {{ store.currentPatient.mrn }}
        </p>
      </div>

      <div class="grid gap-6 md:grid-cols-2">
        <div class="rounded-lg border p-6">
          <h2 class="text-lg font-semibold mb-4">Demographics</h2>
          <dl class="space-y-3">
            <div>
              <dt class="text-sm text-muted-foreground">Given Name</dt>
              <dd>{{ store.currentPatient.given_name }}</dd>
            </div>
            <div>
              <dt class="text-sm text-muted-foreground">Family Name</dt>
              <dd>{{ store.currentPatient.family_name }}</dd>
            </div>
            <div>
              <dt class="text-sm text-muted-foreground">Birth Date</dt>
              <dd>{{ store.currentPatient.birth_date || 'Not recorded' }}</dd>
            </div>
          </dl>
        </div>

        <div class="rounded-lg border p-6">
          <h2 class="text-lg font-semibold mb-4">System Info</h2>
          <dl class="space-y-3">
            <div>
              <dt class="text-sm text-muted-foreground">Patient ID</dt>
              <dd class="font-mono text-sm">{{ store.currentPatient.id }}</dd>
            </div>
            <div>
              <dt class="text-sm text-muted-foreground">EHR ID</dt>
              <dd class="font-mono text-sm">{{ store.currentPatient.ehr_id }}</dd>
            </div>
            <div>
              <dt class="text-sm text-muted-foreground">Created</dt>
              <dd>{{ new Date(store.currentPatient.created_at).toLocaleString() }}</dd>
            </div>
          </dl>
        </div>
      </div>

      <div class="grid gap-4 md:grid-cols-3">
        <div class="rounded-lg border p-6 opacity-50">
          <h3 class="font-semibold">Recent Encounters</h3>
          <p class="text-sm text-muted-foreground mt-1">Coming soon</p>
        </div>
        <div class="rounded-lg border p-6 opacity-50">
          <h3 class="font-semibold">Vital Signs</h3>
          <p class="text-sm text-muted-foreground mt-1">Coming soon</p>
        </div>
        <div class="rounded-lg border p-6 opacity-50">
          <h3 class="font-semibold">Medications</h3>
          <p class="text-sm text-muted-foreground mt-1">Coming soon</p>
        </div>
      </div>
    </div>

    <div v-else class="text-center py-8">
      <p class="text-muted-foreground">Patient not found</p>
    </div>
  </div>
</template>
