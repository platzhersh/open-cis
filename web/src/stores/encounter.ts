import { defineStore } from 'pinia'
import { ref } from 'vue'
import { api } from '@/lib/api'
import type { Encounter, EncounterCreate, EncounterUpdate } from '@/types'

export const useEncounterStore = defineStore('encounter', () => {
  const encounters = ref<Encounter[]>([])
  const currentEncounter = ref<Encounter | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  async function fetchEncounters(patientId?: string) {
    loading.value = true
    error.value = null
    try {
      const params = patientId ? { patient_id: patientId } : {}
      encounters.value = await api.get<Encounter[]>('/api/encounters', { params })
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to fetch encounters'
    } finally {
      loading.value = false
    }
  }

  async function fetchEncounter(id: string) {
    loading.value = true
    error.value = null
    try {
      currentEncounter.value = await api.get<Encounter>(`/api/encounters/${id}`)
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to fetch encounter'
      currentEncounter.value = null
    } finally {
      loading.value = false
    }
  }

  async function createEncounter(data: EncounterCreate): Promise<Encounter | null> {
    loading.value = true
    error.value = null
    try {
      const encounter = await api.post<Encounter>('/api/encounters', data)
      encounters.value.unshift(encounter) // Add to beginning (sorted by start_time desc)
      return encounter
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to create encounter'
      return null
    } finally {
      loading.value = false
    }
  }

  async function updateEncounter(id: string, data: EncounterUpdate): Promise<Encounter | null> {
    loading.value = true
    error.value = null
    try {
      const encounter = await api.patch<Encounter>(`/api/encounters/${id}`, data)
      // Update in local state
      const index = encounters.value.findIndex((e) => e.id === id)
      if (index !== -1) {
        encounters.value[index] = encounter
      }
      if (currentEncounter.value?.id === id) {
        currentEncounter.value = encounter
      }
      return encounter
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to update encounter'
      return null
    } finally {
      loading.value = false
    }
  }

  async function deleteEncounter(id: string): Promise<boolean> {
    loading.value = true
    error.value = null
    try {
      await api.delete(`/api/encounters/${id}`)
      // Remove from local state
      encounters.value = encounters.value.filter((e) => e.id !== id)
      if (currentEncounter.value?.id === id) {
        currentEncounter.value = null
      }
      return true
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to delete encounter'
      return false
    } finally {
      loading.value = false
    }
  }

  return {
    encounters,
    currentEncounter,
    loading,
    error,
    fetchEncounters,
    fetchEncounter,
    createEncounter,
    updateEncounter,
    deleteEncounter,
  }
})
