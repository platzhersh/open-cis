import { defineStore } from 'pinia'
import { ref } from 'vue'
import { api } from '@/lib/api'
import type { SystemInfo } from '@/types'

export const useSystemStore = defineStore('system', () => {
  const systemInfo = ref<SystemInfo | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  async function fetchSystemInfo() {
    loading.value = true
    error.value = null
    try {
      systemInfo.value = await api.get<SystemInfo>('/api/system')
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to fetch system info'
    } finally {
      loading.value = false
    }
  }

  return { systemInfo, loading, error, fetchSystemInfo }
})
