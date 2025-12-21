import { defineStore } from 'pinia'
import { ref } from 'vue'
import { api } from '@/lib/api'
import type { Patient, PatientCreate } from '@/types'

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
    currentPatient,
    loading,
    error,
    fetchPatients,
    fetchPatient,
    createPatient,
  }
})
