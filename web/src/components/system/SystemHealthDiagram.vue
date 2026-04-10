<script setup lang="ts">
import type { HealthChecksSection, TerminologySection } from '@/types'

defineProps<{
  healthChecks: HealthChecksSection
  terminology: TerminologySection
}>()

function statusColor(itemStatus: string): string {
  return itemStatus === 'ok' ? 'bg-green-500' : 'bg-red-500'
}

function statusLabel(item: { status: string; data: { status: string } | null }): string {
  if (item.data) {
    const s = item.data.status
    return s.charAt(0).toUpperCase() + s.slice(1)
  }
  return 'Unavailable'
}

function terminologyStatusColor(status: string): string {
  if (status === 'ok') return 'bg-green-500'
  if (status === 'partial') return 'bg-yellow-500'
  return 'bg-red-500'
}

function terminologyLabel(section: TerminologySection): string {
  if (section.status === 'ok') return 'Online'
  if (section.status === 'partial') return 'Degraded'
  return 'Offline'
}

function terminologyHostname(section: TerminologySection): string {
  if (!section.data?.url) return 'Not configured'
  try {
    const url = new URL(section.data.url)
    if (url.hostname === 'tx.fhir.ch') return 'tx.fhir.ch (Swiss)'
    if (['localhost', '127.0.0.1'].includes(url.hostname) || url.hostname.startsWith('snowstorm'))
      return 'Self-hosted'
    return url.hostname
  } catch {
    return section.data.url
  }
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
        <span class="text-muted-foreground">&rarr;</span>
        <div class="flex items-center gap-2 rounded-md border px-4 py-3 min-w-[140px]">
          <span class="h-2.5 w-2.5 rounded-full shrink-0" :class="statusColor(healthChecks.data.api.status)" />
          <div>
            <p class="text-sm font-medium">API</p>
            <p class="text-xs text-muted-foreground">{{ statusLabel(healthChecks.data.api) }}</p>
          </div>
        </div>
        <span class="text-muted-foreground">&rarr;</span>
        <div class="flex items-center gap-2 rounded-md border px-4 py-3 min-w-[140px]">
          <span class="h-2.5 w-2.5 rounded-full shrink-0" :class="statusColor(healthChecks.data.database.status)" />
          <div>
            <p class="text-sm font-medium">App Database</p>
            <p class="text-xs text-muted-foreground">{{ statusLabel(healthChecks.data.database) }}</p>
          </div>
        </div>
      </div>

      <!-- Connection line from API down to EHRBase row -->
      <div class="flex items-center gap-3">
        <div class="min-w-[140px]" />
        <span class="invisible">&rarr;</span>
        <div class="min-w-[140px] flex justify-center">
          <span class="text-muted-foreground">&darr;</span>
        </div>
      </div>

      <!-- Row 2: EHRBase → EHRBase DB -->
      <div class="flex items-center gap-3">
        <div class="min-w-[140px]" />
        <span class="invisible">&rarr;</span>
        <div class="flex items-center gap-2 rounded-md border px-4 py-3 min-w-[140px]">
          <span class="h-2.5 w-2.5 rounded-full shrink-0" :class="statusColor(healthChecks.data.ehrbase.status)" />
          <div>
            <p class="text-sm font-medium">EHRBase</p>
            <p class="text-xs text-muted-foreground">{{ statusLabel(healthChecks.data.ehrbase) }}</p>
          </div>
        </div>
        <span class="text-muted-foreground">&rarr;</span>
        <div class="flex items-center gap-2 rounded-md border px-4 py-3 min-w-[140px]">
          <span class="h-2.5 w-2.5 rounded-full shrink-0" :class="statusColor(healthChecks.data.ehrbase.status)" />
          <div>
            <p class="text-sm font-medium">EHRBase DB</p>
            <p class="text-xs text-muted-foreground">{{ statusLabel(healthChecks.data.ehrbase) }}</p>
          </div>
        </div>
      </div>

      <!-- Connection line from API down to Terminology row -->
      <div class="flex items-center gap-3">
        <div class="min-w-[140px]" />
        <span class="invisible">&rarr;</span>
        <div class="min-w-[140px] flex justify-center">
          <span class="text-muted-foreground">&darr;</span>
        </div>
      </div>

      <!-- Row 3: Terminology Server -->
      <div class="flex items-center gap-3">
        <div class="min-w-[140px]" />
        <span class="invisible">&rarr;</span>
        <div class="flex items-center gap-2 rounded-md border px-4 py-3 min-w-[140px]">
          <span class="h-2.5 w-2.5 rounded-full shrink-0" :class="terminologyStatusColor(terminology.status)" />
          <div>
            <p class="text-sm font-medium">Terminology</p>
            <p class="text-xs text-muted-foreground">{{ terminologyLabel(terminology) }}</p>
          </div>
        </div>
        <span class="text-muted-foreground text-xs">&larr;</span>
        <div class="text-xs text-muted-foreground">
          <p>{{ terminologyHostname(terminology) }}</p>
          <p v-if="terminology.data?.response_ms != null">{{ terminology.data.response_ms }}ms</p>
        </div>
      </div>
    </div>

    <!-- Mobile: stacked cards -->
    <div class="md:hidden space-y-2">
      <div
        v-for="item in [
          { name: 'Frontend', status: 'ok' as const, desc: 'Vue 3 + Vite', label: 'Available' },
          { name: 'API', status: healthChecks.data.api.status, desc: 'FastAPI', label: statusLabel(healthChecks.data.api) },
          { name: 'App Database', status: healthChecks.data.database.status, desc: 'PostgreSQL', label: statusLabel(healthChecks.data.database) },
          { name: 'EHRBase', status: healthChecks.data.ehrbase.status, desc: 'openEHR CDR', label: statusLabel(healthChecks.data.ehrbase) },
          { name: 'EHRBase DB', status: healthChecks.data.ehrbase.status, desc: 'PostgreSQL', label: statusLabel(healthChecks.data.ehrbase) },
          { name: 'Terminology', status: terminology.status === 'ok' ? 'ok' as const : 'error' as const, desc: terminologyHostname(terminology), label: terminologyLabel(terminology) },
        ]"
        :key="item.name"
        class="flex items-center gap-2 rounded-md border px-4 py-3"
      >
        <span class="h-2.5 w-2.5 rounded-full shrink-0" :class="statusColor(item.status)" />
        <div class="flex-1">
          <p class="text-sm font-medium">{{ item.name }}</p>
          <p class="text-xs text-muted-foreground">{{ item.desc }}</p>
        </div>
        <span class="text-xs text-muted-foreground">{{ item.label }}</span>
      </div>
    </div>
  </div>
</template>
