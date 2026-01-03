<script setup lang="ts">
import { RouterView } from 'vue-router'
import { Github } from 'lucide-vue-next'
</script>

<template>
  <div class="min-h-screen bg-background">
    <header class="border-b">
      <div class="container flex h-16 items-center justify-between px-4">
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
          <RouterLink
            to="/encounters"
            class="text-sm font-medium text-muted-foreground transition-colors hover:text-primary"
          >
            Encounters
          </RouterLink>
        </nav>
        <a
          href="https://github.com/platzhersh/open-cis"
          target="_blank"
          rel="noopener noreferrer"
          class="flex items-center gap-2 text-sm font-medium text-muted-foreground transition-colors hover:text-primary"
          title="View source code on GitHub"
        >
          <Github :size="18" />
          <span>Open Source</span>
        </a>
      </div>
    </header>
    <main class="container py-6">
      <RouterView />
    </main>
  </div>
</template>
