import { defineStore } from 'pinia'
import { ref } from 'vue'
import { api } from '@/lib/api'
import type {
  VitalSignsReading,
  VitalSignsCreate,
  VitalSignsListResponse,
  RawComposition,
  CompositionPathsResponse,
  ArchetypeInfo,
} from '@/types'

export const useVitalsStore = defineStore('vitals', () => {
  const readings = ref<VitalSignsReading[]>([])
  const currentReading = ref<VitalSignsReading | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)
  const total = ref(0)

  async function fetchVitals(
    patientId: string,
    options?: { fromDate?: string; toDate?: string; skip?: number; limit?: number }
  ) {
    loading.value = true
    error.value = null
    try {
      const params: Record<string, string | number> = { patient_id: patientId }
      if (options?.fromDate) params.from_date = options.fromDate
      if (options?.toDate) params.to_date = options.toDate
      if (options?.skip !== undefined) params.skip = options.skip
      if (options?.limit !== undefined) params.limit = options.limit

      const result = await api.get<VitalSignsListResponse>('/api/observations/vital-signs', params)
      readings.value = result.items
      total.value = result.total
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to fetch vital signs'
      readings.value = []
      total.value = 0
    } finally {
      loading.value = false
    }
  }

  async function recordVitals(data: VitalSignsCreate): Promise<VitalSignsReading | null> {
    loading.value = true
    error.value = null
    try {
      const reading = await api.post<VitalSignsReading>('/api/observations/vital-signs', data)
      readings.value.unshift(reading) // Add to beginning (most recent first)
      total.value += 1
      return reading
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to record vital signs'
      return null
    } finally {
      loading.value = false
    }
  }

  async function deleteVitals(compositionUid: string, patientId: string): Promise<boolean> {
    loading.value = true
    error.value = null
    try {
      await api.delete(`/api/observations/vital-signs/${encodeURIComponent(compositionUid)}?patient_id=${encodeURIComponent(patientId)}`)
      readings.value = readings.value.filter((r) => r.id !== compositionUid)
      total.value = Math.max(0, total.value - 1)
      if (currentReading.value?.id === compositionUid) {
        currentReading.value = null
      }
      return true
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to delete vital signs'
      return false
    } finally {
      loading.value = false
    }
  }

  async function fetchRawComposition(
    compositionUid: string,
    patientId: string,
    format: 'FLAT' | 'STRUCTURED' = 'FLAT'
  ): Promise<RawComposition | null> {
    try {
      return await api.get<RawComposition>(
        `/api/observations/openehr/compositions/${encodeURIComponent(compositionUid)}`,
        { patient_id: patientId, format }
      )
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to fetch composition'
      return null
    }
  }

  async function fetchCompositionPaths(
    compositionUid: string,
    patientId: string
  ): Promise<CompositionPathsResponse | null> {
    try {
      return await api.get<CompositionPathsResponse>(
        `/api/observations/openehr/compositions/${encodeURIComponent(compositionUid)}/paths`,
        { patient_id: patientId }
      )
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to fetch composition paths'
      return null
    }
  }

  async function fetchArchetypeInfo(archetypeId: string): Promise<ArchetypeInfo | null> {
    try {
      return await api.get<ArchetypeInfo>(
        `/api/observations/openehr/archetypes/${encodeURIComponent(archetypeId)}`
      )
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to fetch archetype info'
      return null
    }
  }

  function setCurrentReading(reading: VitalSignsReading | null) {
    currentReading.value = reading
  }

  function clearReadings() {
    readings.value = []
    currentReading.value = null
    total.value = 0
    error.value = null
  }

  return {
    readings,
    currentReading,
    loading,
    error,
    total,
    fetchVitals,
    recordVitals,
    deleteVitals,
    fetchRawComposition,
    fetchCompositionPaths,
    fetchArchetypeInfo,
    setCurrentReading,
    clearReadings,
  }
})
