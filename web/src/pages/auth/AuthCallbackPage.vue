<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { Loader2 } from 'lucide-vue-next'
import { exchangeCodeForToken } from '@/lib/oidc'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()

const error = ref<string | null>(null)

onMounted(async () => {
  const code = route.query.code as string | undefined
  const codeVerifier = sessionStorage.getItem('oidc_code_verifier')

  if (!code) {
    error.value = 'No authorization code received. Please try logging in again.'
    return
  }

  if (!codeVerifier) {
    error.value = 'Login session expired. Please try again.'
    return
  }

  try {
    const token = await exchangeCodeForToken(code, codeVerifier)
    sessionStorage.removeItem('oidc_code_verifier')
    auth.setToken(token)

    const success = await auth.fetchMe()
    if (success) {
      router.replace('/')
    } else {
      error.value = 'Failed to load user profile. Please try again.'
    }
  } catch (e) {
    error.value = e instanceof Error ? e.message : 'Authentication failed'
  }
})
</script>

<template>
  <div class="min-h-screen flex items-center justify-center bg-background px-4">
    <div class="text-center space-y-4">
      <div v-if="!error">
        <Loader2 class="h-8 w-8 animate-spin mx-auto mb-4 text-muted-foreground" />
        <p class="text-sm text-muted-foreground">Completing sign in...</p>
      </div>

      <div v-else class="max-w-sm space-y-4">
        <div class="rounded-md border border-destructive/50 bg-destructive/10 p-4 text-sm text-destructive">
          {{ error }}
        </div>
        <RouterLink
          to="/login"
          class="inline-flex items-center justify-center rounded-md text-sm font-medium bg-primary text-primary-foreground h-10 px-4 py-2 hover:bg-primary/90"
        >
          Back to Login
        </RouterLink>
      </div>
    </div>
  </div>
</template>
