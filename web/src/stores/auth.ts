import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { api } from '@/lib/api'

export interface CurrentUser {
  id: string
  email: string
  name: string
  role: 'ADMIN' | 'CLINICIAN' | 'NURSE' | 'READONLY'
}

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string | null>(localStorage.getItem('oidc_token'))
  const user = ref<CurrentUser | null>(null)

  const isAuthenticated = computed(() => !!token.value)
  const isAdmin = computed(() => user.value?.role === 'ADMIN')
  const canWrite = computed(() =>
    !!user.value && ['ADMIN', 'CLINICIAN', 'NURSE'].includes(user.value.role),
  )

  function setToken(newToken: string) {
    token.value = newToken
    localStorage.setItem('oidc_token', newToken)
  }

  function clearAuth() {
    token.value = null
    user.value = null
    localStorage.removeItem('oidc_token')
  }

  async function fetchMe(): Promise<boolean> {
    try {
      const data = await api.get<CurrentUser>('/api/auth/me')
      user.value = data
      return true
    } catch {
      clearAuth()
      return false
    }
  }

  return { token, user, isAuthenticated, isAdmin, canWrite, setToken, clearAuth, fetchMe }
})
