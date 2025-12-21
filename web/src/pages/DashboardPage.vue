<script setup lang="ts">
import { RouterLink } from 'vue-router'
</script>

<template>
  <div class="space-y-6">
    <div>
      <h1 class="text-3xl font-bold tracking-tight">
        Dashboard
      </h1>
      <p class="text-muted-foreground">
        Welcome to Open CIS - Clinical Information System
      </p>
    </div>

    <div class="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
      <RouterLink
        to="/patients"
        class="block p-6 bg-card rounded-lg border hover:border-primary transition-colors"
      >
        <h3 class="text-lg font-semibold">
          Patients
        </h3>
        <p class="text-sm text-muted-foreground mt-1">
          View and manage patient records
        </p>
      </RouterLink>

      <div class="p-6 bg-card rounded-lg border opacity-50">
        <h3 class="text-lg font-semibold">
          Encounters
        </h3>
        <p class="text-sm text-muted-foreground mt-1">
          Clinical encounters and visits
        </p>
        <span class="text-xs text-muted-foreground">(Coming soon)</span>
      </div>

      <div class="p-6 bg-card rounded-lg border opacity-50">
        <h3 class="text-lg font-semibold">
          Observations
        </h3>
        <p class="text-sm text-muted-foreground mt-1">
          Vital signs and measurements
        </p>
        <span class="text-xs text-muted-foreground">(Coming soon)</span>
      </div>
    </div>

    <div class="rounded-lg border p-6">
      <h2 class="text-xl font-semibold mb-4">
        About Open CIS
      </h2>
      <p class="text-muted-foreground">
        Open CIS is a minimal Clinical Information System built on openEHR/EHRBase
        for learning and experimentation with clinical data architecture.
      </p>
      <ul class="mt-4 space-y-2 text-sm text-muted-foreground">
        <li>• EHRBase for clinical data storage (openEHR)</li>
        <li>• PostgreSQL for application data (users, audit logs)</li>
        <li>• FastAPI backend with async Python</li>
        <li>• Vue 3 frontend with TypeScript</li>
      </ul>
    </div>
  </div>
</template>
