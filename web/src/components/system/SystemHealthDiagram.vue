<script setup lang="ts">
import type { SystemHealth } from '@/types'

const props = defineProps<{
  health: SystemHealth
}>()

function statusColor(status: string): string {
  switch (status) {
    case 'healthy':
    case 'connected':
    case 'available':
      return 'bg-green-500'
    case 'degraded':
      return 'bg-yellow-500'
    default:
      return 'bg-red-500'
  }
}

function statusLabel(status: string): string {
  return status.charAt(0).toUpperCase() + status.slice(1)
}


</script>

<template>
  <div class="rounded-lg border p-6">
    <h2 class="text-lg font-semibold mb-4">System Architecture</h2>

    <!-- Desktop diagram -->
    <div class="hidden md:block space-y-4">
      <!-- Row 1: Frontend → API → App DB -->
      <div class="flex items-center gap-3">
        <div class="flex items-center gap-2 rounded-md border px-4 py-3 min-w-[140px]">
          <span class="h-2.5 w-2.5 rounded-full bg-green-500 shrink-0" />
          <div>
            <p class="text-sm font-medium">Frontend</p>
            <p class="text-xs text-muted-foreground">Vue 3 + Vite</p>
          </div>
        </div>
        <span class="text-muted-foreground">→</span>
        <div class="flex items-center gap-2 rounded-md border px-4 py-3 min-w-[140px]">
          <span class="h-2.5 w-2.5 rounded-full shrink-0" :class="statusColor(health.api)" />
          <div>
            <p class="text-sm font-medium">API</p>
            <p class="text-xs text-muted-foreground">{{ statusLabel(health.api) }}</p>
          </div>
        </div>
        <span class="text-muted-foreground">→</span>
        <div class="flex items-center gap-2 rounded-md border px-4 py-3 min-w-[140px]">
          <span class="h-2.5 w-2.5 rounded-full shrink-0" :class="statusColor(health.database)" />
          <div>
            <p class="text-sm font-medium">App Database</p>
            <p class="text-xs text-muted-foreground">{{ statusLabel(health.database) }}</p>
          </div>
        </div>
      </div>

      <!-- Connection line from API down to EHRBase row -->
      <div class="flex items-center gap-3">
        <div class="min-w-[140px]" />
        <span class="invisible">→</span>
        <div class="min-w-[140px] flex justify-center">
          <span class="text-muted-foreground">↓</span>
        </div>
      </div>

      <!-- Row 2: EHRBase → EHRBase DB -->
      <div class="flex items-center gap-3">
        <div class="min-w-[140px]" />
        <span class="invisible">→</span>
        <div class="flex items-center gap-2 rounded-md border px-4 py-3 min-w-[140px]">
          <span class="h-2.5 w-2.5 rounded-full shrink-0" :class="statusColor(health.ehrbase)" />
          <div>
            <p class="text-sm font-medium">EHRBase</p>
            <p class="text-xs text-muted-foreground">{{ statusLabel(health.ehrbase) }}</p>
          </div>
        </div>
        <span class="text-muted-foreground">→</span>
        <div class="flex items-center gap-2 rounded-md border px-4 py-3 min-w-[140px]">
          <span class="h-2.5 w-2.5 rounded-full shrink-0" :class="statusColor(health.ehrbase)" />
          <div>
            <p class="text-sm font-medium">EHRBase DB</p>
            <p class="text-xs text-muted-foreground">{{ statusLabel(health.ehrbase) }}</p>
          </div>
        </div>
      </div>
    </div>

    <!-- Mobile: stacked cards -->
    <div class="md:hidden space-y-2">
      <div
        v-for="item in [
          { name: 'Frontend', status: 'available', desc: 'Vue 3 + Vite' },
          { name: 'API', status: health.api, desc: 'FastAPI' },
          { name: 'App Database', status: health.database, desc: 'PostgreSQL' },
          { name: 'EHRBase', status: health.ehrbase, desc: 'openEHR CDR' },
          { name: 'EHRBase DB', status: health.ehrbase, desc: 'PostgreSQL' },
        ]"
        :key="item.name"
        class="flex items-center gap-2 rounded-md border px-4 py-3"
      >
        <span class="h-2.5 w-2.5 rounded-full shrink-0" :class="statusColor(item.status)" />
        <div class="flex-1">
          <p class="text-sm font-medium">{{ item.name }}</p>
          <p class="text-xs text-muted-foreground">{{ item.desc }}</p>
        </div>
        <span class="text-xs text-muted-foreground">{{ statusLabel(item.status) }}</span>
      </div>
    </div>
  </div>
</template>
