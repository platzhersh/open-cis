import { ref } from 'vue'
import { api } from '@/lib/api'
import type { Patient, PatientCreate } from '@/types'

export function usePatients() {
  const patients = ref<Patient[]>([])
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

  async function createPatient(data: PatientCreate): Promise<Patient | null> {
    loading.value = true
    error.value = null
    try {
      const patient = await api.post<Patient>('/api/patients', data)
      patients.value.push(patient)
      return patient
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to create patient'
      return null
    } finally {
      loading.value = false
    }
  }

  return {
    patients,
    loading,
    error,
    fetchPatients,
    createPatient,
  }
}
