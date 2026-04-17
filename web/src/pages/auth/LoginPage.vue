<script setup lang="ts">
import { ref } from 'vue'
import { Loader2, LogIn } from 'lucide-vue-next'
import { generateCodeVerifier, generateCodeChallenge } from '@/lib/pkce'
import { generateState, OIDC_AUTH_ENDPOINT, OIDC_CLIENT_ID, OIDC_REDIRECT_URI } from '@/lib/oidc'
import DemoCredentialRow from '@/components/auth/DemoCredentialRow.vue'

const isDemoMode = import.meta.env.VITE_APP_MODE === 'demo'
const loading = ref(false)
const error = ref<string | null>(null)

async function startLogin() {
  loading.value = true
  error.value = null
  try {
    const codeVerifier = generateCodeVerifier()
    const codeChallenge = await generateCodeChallenge(codeVerifier)
    const state = generateState()

    // Store verifier and state for the callback
    sessionStorage.setItem('oidc_code_verifier', codeVerifier)
    sessionStorage.setItem('oidc_state', state)

    const params = new URLSearchParams({
      response_type: 'code',
      client_id: OIDC_CLIENT_ID,
      redirect_uri: OIDC_REDIRECT_URI,
      scope: 'openid email profile',
      code_challenge: codeChallenge,
      code_challenge_method: 'S256',
      state,
    })

    window.location.href = `${OIDC_AUTH_ENDPOINT}?${params.toString()}`
  } catch (e) {
    error.value = e instanceof Error ? e.message : 'Failed to start login'
    loading.value = false
  }
}
</script>

<template>
  <div class="min-h-screen flex items-center justify-center bg-background px-4">
    <div class="w-full max-w-sm space-y-6">
      <!-- Logo & Title -->
      <div class="text-center space-y-2">
        <div class="flex justify-center">
          <svg width="48" height="48" viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M20 65L50 80L80 65V50L50 65L20 50V65Z" fill="#F39200"/>
            <path d="M50 35L80 50L50 65L20 50L50 35Z" fill="#F39200" fill-opacity="0.8"/>
            <path d="M20 40L50 55L80 40V25L50 40L20 25V40Z" fill="currentColor" class="text-[#005EB8] dark:text-white"/>
            <path d="M50 10L80 25L50 40L20 25L50 10Z" fill="currentColor" fill-opacity="0.8" class="text-[#005EB8] dark:text-white"/>
          </svg>
        </div>
        <h1 class="text-2xl tracking-tighter">
          <span class="font-light">open</span><span class="font-black text-primary">cis</span>
        </h1>
        <p class="text-sm text-muted-foreground">
          Sign in to access the Clinical Information System
        </p>
      </div>

      <!-- Error -->
      <div
        v-if="error"
        class="rounded-md border border-destructive/50 bg-destructive/10 p-3 text-sm text-destructive"
      >
        {{ error }}
      </div>

      <!-- Sign In Button -->
      <button
        class="inline-flex w-full items-center justify-center rounded-md text-sm font-medium bg-primary text-primary-foreground h-11 px-4 py-2 hover:bg-primary/90 disabled:opacity-50 disabled:pointer-events-none"
        :disabled="loading"
        @click="startLogin"
      >
        <Loader2 v-if="loading" class="h-4 w-4 mr-2 animate-spin" />
        <LogIn v-else class="h-4 w-4 mr-2" />
        Sign in with OIDC
      </button>

      <!-- Demo Credentials -->
      <div
        v-if="isDemoMode"
        class="rounded-lg border border-dashed p-4 text-sm"
      >
        <p class="font-medium text-muted-foreground mb-3">Demo accounts</p>
        <div class="space-y-2">
          <DemoCredentialRow
            label="Clinician"
            email="clinician@open-cis.local"
            password="clinician"
          />
          <DemoCredentialRow
            label="Admin"
            email="admin@open-cis.local"
            password="admin"
          />
        </div>
      </div>
    </div>
  </div>
</template>
