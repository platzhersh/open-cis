<script setup lang="ts">
import { onMounted, onUnmounted, ref } from 'vue'
import { Loader2, RefreshCw } from 'lucide-vue-next'
import { useSystemStore } from '@/stores/system'
import SystemHealthDiagram from '@/components/system/SystemHealthDiagram.vue'
import TemplateList from '@/components/system/TemplateList.vue'

const frontendVersion = __APP_VERSION__

const store = useSystemStore()
const autoRefresh = ref(false)
let intervalId: number | null = null

function toggleAutoRefresh() {
  autoRefresh.value = !autoRefresh.value
  if (autoRefresh.value) {
    intervalId = window.setInterval(() => store.fetchSystemInfo(), 30000)
  } else if (intervalId) {
    window.clearInterval(intervalId)
    intervalId = null
  }
}

onMounted(() => {
  store.fetchSystemInfo()
})

onUnmounted(() => {
  if (intervalId) window.clearInterval(intervalId)
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
      <SystemHealthDiagram
        :health-checks="store.systemInfo.healthChecks"
        :terminology="store.systemInfo.terminology"
      />

      <!-- Version Info + Data Stats -->
      <div class="grid gap-6 md:grid-cols-2">
        <!-- Versions -->
        <div class="rounded-lg border p-4 space-y-3">
          <h2 class="text-lg font-semibold">Versions</h2>
          <div v-if="store.systemInfo.version.data" class="space-y-2">
            <div class="flex justify-between text-sm">
              <span class="text-muted-foreground">API</span>
              <span class="font-mono">{{ store.systemInfo.version.data.api }}</span>
            </div>
            <div class="flex justify-between text-sm">
              <span class="text-muted-foreground">EHRBase</span>
              <span class="font-mono">{{ store.systemInfo.version.data.ehrbase ?? 'N/A' }}</span>
            </div>
            <div class="flex justify-between text-sm">
              <span class="text-muted-foreground">Frontend</span>
              <span class="font-mono">{{ frontendVersion }}</span>
            </div>
          </div>
          <p v-else class="text-sm text-muted-foreground">
            {{ store.systemInfo.version.error?.message ?? 'Could not determine versions' }}
          </p>
          <!-- Terminology Server Info -->
          <div v-if="store.systemInfo.terminology.data" class="border-t pt-3 mt-3 space-y-2">
            <h3 class="text-sm font-medium">Terminology Server</h3>
            <div class="flex justify-between text-sm">
              <span class="text-muted-foreground">URL</span>
              <span class="font-mono text-xs truncate max-w-[200px]">{{ store.systemInfo.terminology.data.url }}</span>
            </div>
            <div v-if="store.systemInfo.terminology.data.response_ms != null" class="flex justify-between text-sm">
              <span class="text-muted-foreground">Response</span>
              <span class="font-mono">{{ store.systemInfo.terminology.data.response_ms }}ms</span>
            </div>
          </div>
        </div>

        <!-- Data Stats -->
        <div class="rounded-lg border p-4 space-y-3">
          <h2 class="text-lg font-semibold">Data Statistics</h2>
          <div v-if="store.systemInfo.dbCounts.data" class="space-y-2">
            <div class="flex justify-between text-sm">
              <span class="text-muted-foreground">Patients</span>
              <span class="font-mono">{{ store.systemInfo.dbCounts.data.patients }}</span>
            </div>
            <div class="flex justify-between text-sm">
              <span class="text-muted-foreground">Encounters</span>
              <span class="font-mono">{{ store.systemInfo.dbCounts.data.encounters }}</span>
            </div>
            <div class="flex justify-between text-sm">
              <span class="text-muted-foreground">Audit Logs</span>
              <span class="font-mono">{{ store.systemInfo.dbCounts.data.audit_logs }}</span>
            </div>
          </div>
          <p v-else class="text-sm text-muted-foreground">
            {{ store.systemInfo.dbCounts.error?.message ?? 'Database unavailable' }}
          </p>
        </div>
      </div>

      <!-- Templates Table -->
      <TemplateList :section="store.systemInfo.templates" />
    </template>
  </div>
</template>
