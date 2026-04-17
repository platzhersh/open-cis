import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { api, ApiRequestError } from '@/lib/api'

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

  /**
   * Fetch the current user profile.
   * Returns true on success, false on auth failure (401/403).
   * Throws on network/server errors to allow retry.
   */
  async function fetchMe(): Promise<boolean> {
    try {
      const data = await api.get<CurrentUser>('/api/auth/me')
      user.value = data
      return true
    } catch (e) {
      if (e instanceof ApiRequestError && (e.status === 401 || e.status === 403)) {
        clearAuth()
        return false
      }
      // Network or server error — don't clear auth, propagate for retry
      throw e
    }
  }

  return { token, user, isAuthenticated, isAdmin, canWrite, setToken, clearAuth, fetchMe }
})
