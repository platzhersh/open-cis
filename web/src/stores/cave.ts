import { defineStore } from 'pinia'
import { ref } from 'vue'
import { api } from '@/lib/api'
import type {
  CaveEntry,
  CaveEntryCreate,
  CaveEntryUpdate,
  CaveListResponse,
  CaveSummary,
} from '@/types/cave'

export const useCaveStore = defineStore('cave', () => {
  const entries = ref<CaveEntry[]>([])
  const summary = ref<CaveSummary | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)
  const total = ref(0)

  async function fetchEntries(patientId: string, status?: string, category?: string) {
    loading.value = true
    error.value = null
    entries.value = []
    total.value = 0
    try {
      const params: Record<string, string> = { patient_id: patientId }
      if (status) params.status = status
      if (category) params.category = category

      const result = await api.get<CaveListResponse>('/api/cave', params)
      entries.value = result.items
      total.value = result.total
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to fetch CAVE entries'
      entries.value = []
      total.value = 0
    } finally {
      loading.value = false
    }
  }

  async function fetchSummary(patientId: string) {
    loading.value = true
    error.value = null
    summary.value = null
    try {
      summary.value = await api.get<CaveSummary>(`/api/cave/summary/${encodeURIComponent(patientId)}`)
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to fetch CAVE summary'
      summary.value = null
    } finally {
      loading.value = false
    }
  }

  async function createEntry(data: CaveEntryCreate): Promise<CaveEntry | null> {
    loading.value = true
    error.value = null
    try {
      const entry = await api.post<CaveEntry>('/api/cave', data)
      entries.value.unshift(entry)
      total.value += 1
      return entry
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to create CAVE entry'
      return null
    } finally {
      loading.value = false
    }
  }

  async function updateEntry(
    compositionUid: string,
    patientId: string,
    data: CaveEntryUpdate
  ): Promise<CaveEntry | null> {
    loading.value = true
    error.value = null
    try {
      const entry = await api.patch<CaveEntry>(
        `/api/cave/${encodeURIComponent(compositionUid)}?patient_id=${encodeURIComponent(patientId)}`,
        data
      )
      const index = entries.value.findIndex((e) => e.id === compositionUid)
      if (index !== -1) {
        entries.value[index] = entry
      }
      return entry
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to update CAVE entry'
      return null
    } finally {
      loading.value = false
    }
  }

  async function deleteEntry(compositionUid: string, patientId: string): Promise<boolean> {
    loading.value = true
    error.value = null
    try {
      await api.delete(
        `/api/cave/${encodeURIComponent(compositionUid)}?patient_id=${encodeURIComponent(patientId)}`
      )
      entries.value = entries.value.filter((e) => e.id !== compositionUid)
      total.value = Math.max(0, total.value - 1)
      return true
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to delete CAVE entry'
      return false
    } finally {
      loading.value = false
    }
  }

  async function recordNka(patientId: string): Promise<boolean> {
    loading.value = true
    error.value = null
    try {
      await api.post('/api/cave/nka', { patient_id: patientId })
      // Refresh summary after recording NKA
      await fetchSummary(patientId)
      return true
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to record NKA'
      return false
    } finally {
      loading.value = false
    }
  }

  async function removeNka(patientId: string): Promise<boolean> {
    loading.value = true
    error.value = null
    try {
      await api.delete(`/api/cave/nka?patient_id=${encodeURIComponent(patientId)}`)
      await fetchSummary(patientId)
      return true
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to remove NKA declaration'
      return false
    } finally {
      loading.value = false
    }
  }

  function clearEntries() {
    entries.value = []
    summary.value = null
    total.value = 0
    error.value = null
  }

  return {
    entries,
    summary,
    loading,
    error,
    total,
    fetchEntries,
    fetchSummary,
    createEntry,
    updateEntry,
    deleteEntry,
    recordNka,
    removeNka,
    clearEntries,
  }
})
