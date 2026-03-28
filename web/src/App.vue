<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { RouterView } from 'vue-router'
import { Github, Moon, Sun } from 'lucide-vue-next'

const version = __APP_VERSION__
const isDark = ref(false)

function toggleDark() {
  isDark.value = !isDark.value
  document.documentElement.classList.toggle('dark', isDark.value)
  localStorage.setItem('theme', isDark.value ? 'dark' : 'light')
}

onMounted(() => {
  const saved = localStorage.getItem('theme')
  isDark.value = saved === 'dark' || (!saved && window.matchMedia('(prefers-color-scheme: dark)').matches)
  document.documentElement.classList.toggle('dark', isDark.value)
})
</script>

<template>
  <div class="min-h-screen bg-background">
    <header class="border-b">
      <div class="container flex h-16 items-center justify-between px-4">
        <nav class="flex items-center space-x-6">
          <RouterLink
            to="/"
            class="flex items-center gap-2"
          >
            <!-- Brand logo mark (isometric brick) -->
            <svg width="28" height="28" viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg" class="shrink-0">
              <path d="M20 65L50 80L80 65V50L50 65L20 50V65Z" fill="#F39200"/>
              <path d="M50 35L80 50L50 65L20 50L50 35Z" fill="#F39200" fill-opacity="0.8"/>
              <path d="M20 40L50 55L80 40V25L50 40L20 25V40Z" fill="currentColor" class="text-[#005EB8] dark:text-white"/>
              <path d="M50 10L80 25L50 40L20 25L50 10Z" fill="currentColor" fill-opacity="0.8" class="text-[#005EB8] dark:text-white"/>
            </svg>
            <!-- Brand wordmark -->
            <span class="text-lg tracking-tighter">
              <span class="font-light">open</span><span class="font-black text-primary">cis</span>
            </span>
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
        <div class="flex items-center gap-4">
          <button
            @click="toggleDark"
            class="inline-flex items-center justify-center rounded-md p-2 text-muted-foreground transition-colors hover:text-primary hover:bg-accent"
            :title="isDark ? 'Switch to light mode' : 'Switch to dark mode'"
          >
            <Sun v-if="isDark" :size="18" />
            <Moon v-else :size="18" />
          </button>
        <span class="text-xs text-muted-foreground/60 font-mono">v{{ version }}</span>
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
      </div>
    </header>
    <main class="container py-6">
      <RouterView />
    </main>
  </div>
</template>
