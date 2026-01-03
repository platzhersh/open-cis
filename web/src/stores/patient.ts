import { defineStore } from 'pinia'
import { ref } from 'vue'
import { api } from '@/lib/api'
import type { Patient, PatientCreate, PatientUpdate, MrnExistsResponse } from '@/types'

export const usePatientStore = defineStore('patient', () => {
  const patients = ref<Patient[]>([])
  const currentPatient = ref<Patient | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  async function fetchPatients() {
    loading.value = true
    error.value = null
    try {
      patients.value = await api.get<Patient[]>('/api/patients')
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to fetch patients'
    } finally {
      loading.value = false
    }
  }

  async function fetchPatient(id: string) {
    loading.value = true
    error.value = null
    try {
      currentPatient.value = await api.get<Patient>(`/api/patients/${id}`)
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to fetch patient'
      currentPatient.value = null
    } finally {
      loading.value = false
    }
  }

  async function createPatient(data: PatientCreate): Promise<Patient | null> {
    loading.value = true
    error.value = null
    try {
      const patient = await api.post<Patient>('/api/patients', data)
      patients.value.unshift(patient) // Add to beginning (sorted by createdAt desc)
      return patient
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to create patient'
      return null
    } finally {
      loading.value = false
    }
  }

  async function updatePatient(id: string, data: PatientUpdate): Promise<Patient | null> {
    loading.value = true
    error.value = null
    try {
      const patient = await api.patch<Patient>(`/api/patients/${id}`, data)
      // Update in local state
      const index = patients.value.findIndex((p) => p.id === id)
      if (index !== -1) {
        patients.value[index] = patient
      }
      if (currentPatient.value?.id === id) {
        currentPatient.value = patient
      }
      return patient
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to update patient'
      return null
    } finally {
      loading.value = false
    }
  }

  async function deletePatient(id: string): Promise<boolean> {
    loading.value = true
    error.value = null
    try {
      await api.delete(`/api/patients/${id}`)
      // Remove from local state
      patients.value = patients.value.filter((p) => p.id !== id)
      if (currentPatient.value?.id === id) {
        currentPatient.value = null
      }
      return true
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to delete patient'
      return false
    } finally {
      loading.value = false
    }
  }

  async function checkMrnExists(mrn: string): Promise<boolean> {
    try {
      const result = await api.get<MrnExistsResponse>(`/api/patients/mrn/${encodeURIComponent(mrn)}/exists`)
      return result.exists
    } catch {
      // On error, assume it doesn't exist (will be caught on submit if it does)
      return false
    }
  }

  return {
    patients,
    currentPatient,
    loading,
    error,
    fetchPatients,
    fetchPatient,
    createPatient,
    updatePatient,
    deletePatient,
    checkMrnExists,
  }
})
