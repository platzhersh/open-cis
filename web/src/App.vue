<script setup lang="ts">
import { RouterView } from 'vue-router'
</script>

<template>
  <div class="min-h-screen bg-background">
    <header class="border-b">
      <div class="container flex h-16 items-center px-4">
        <nav class="flex items-center space-x-6">
          <RouterLink
            to="/"
            class="text-lg font-semibold"
          >
            Open CIS
          </RouterLink>
          <RouterLink
            to="/patients"
            class="text-sm font-medium text-muted-foreground transition-colors hover:text-primary"
          >
            Patients
          </RouterLink>
        </nav>
      </div>
    </header>
    <main class="container py-6">
      <RouterView />
    </main>
  </div>
</template>
