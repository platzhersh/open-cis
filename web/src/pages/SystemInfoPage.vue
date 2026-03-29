<script setup lang="ts">
import { onMounted, onUnmounted, ref } from 'vue'
import { Loader2, RefreshCw } from 'lucide-vue-next'

const frontendVersion = __APP_VERSION__
import { useSystemStore } from '@/stores/system'
import SystemHealthDiagram from '@/components/system/SystemHealthDiagram.vue'
import TemplateList from '@/components/system/TemplateList.vue'

const store = useSystemStore()
const autoRefresh = ref(false)
let intervalId: ReturnType<typeof setInterval> | null = null

function toggleAutoRefresh() {
  autoRefresh.value = !autoRefresh.value
  if (autoRefresh.value) {
    intervalId = setInterval(() => store.fetchSystemInfo(), 30000)
  } else if (intervalId) {
    clearInterval(intervalId)
    intervalId = null
  }
}

onMounted(() => {
  store.fetchSystemInfo()
})

onUnmounted(() => {
  if (intervalId) clearInterval(intervalId)
})
</script>

<template>
  <div class="space-y-6">
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-3xl font-bold tracking-tight">System Info</h1>
        <p class="text-muted-foreground">Component health, versions, and registered templates</p>
      </div>
      <div class="flex items-center gap-3">
        <label class="flex items-center gap-2 text-sm text-muted-foreground">
          <input
            type="checkbox"
            :checked="autoRefresh"
            class="rounded"
            @change="toggleAutoRefresh"
          />
          Auto-refresh
        </label>
        <button
          class="inline-flex items-center justify-center rounded-md text-sm font-medium border h-9 px-3 hover:bg-muted/50 transition-colors"
          :disabled="store.loading"
          @click="store.fetchSystemInfo()"
        >
          <RefreshCw class="h-4 w-4 mr-2" :class="{ 'animate-spin': store.loading }" />
          Refresh
        </button>
      </div>
    </div>

    <div v-if="store.loading && !store.systemInfo" class="text-center py-8">
      <Loader2 class="h-5 w-5 animate-spin mx-auto mb-2 text-muted-foreground" />
      <p class="text-sm text-muted-foreground">Loading system info...</p>
    </div>

    <div v-else-if="store.error && !store.systemInfo" class="rounded-lg border border-destructive p-4">
      <p class="text-destructive">{{ store.error }}</p>
    </div>

    <template v-if="store.systemInfo">
      <!-- Health Diagram -->
      <SystemHealthDiagram :health="store.systemInfo.health" />

      <!-- Version Info + Data Stats -->
      <div class="grid gap-6 md:grid-cols-2">
        <!-- Versions -->
        <div class="rounded-lg border p-4 space-y-3">
          <h2 class="text-lg font-semibold">Versions</h2>
          <div class="space-y-2">
            <div class="flex justify-between text-sm">
              <span class="text-muted-foreground">API</span>
              <span class="font-mono">{{ store.systemInfo.versions.api }}</span>
            </div>
            <div class="flex justify-between text-sm">
              <span class="text-muted-foreground">EHRBase</span>
              <span class="font-mono">{{ store.systemInfo.versions.ehrbase ?? 'N/A' }}</span>
            </div>
            <div class="flex justify-between text-sm">
              <span class="text-muted-foreground">Frontend</span>
              <span class="font-mono">{{ frontendVersion }}</span>
            </div>
          </div>
        </div>

        <!-- Data Stats -->
        <div class="rounded-lg border p-4 space-y-3">
          <h2 class="text-lg font-semibold">Data Statistics</h2>
          <div v-if="store.systemInfo.stats" class="space-y-2">
            <div class="flex justify-between text-sm">
              <span class="text-muted-foreground">Patients</span>
              <span class="font-mono">{{ store.systemInfo.stats.patients }}</span>
            </div>
            <div class="flex justify-between text-sm">
              <span class="text-muted-foreground">Encounters</span>
              <span class="font-mono">{{ store.systemInfo.stats.encounters }}</span>
            </div>
            <div class="flex justify-between text-sm">
              <span class="text-muted-foreground">Audit Logs</span>
              <span class="font-mono">{{ store.systemInfo.stats.audit_logs }}</span>
            </div>
          </div>
          <p v-else class="text-sm text-muted-foreground">
            Database unavailable
          </p>
        </div>
      </div>

      <!-- Templates Table -->
      <TemplateList :templates="store.systemInfo.templates" />
    </template>
  </div>
</template>
