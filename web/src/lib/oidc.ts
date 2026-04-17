/**
 * OIDC configuration derived from environment variables.
 *
 * Endpoints are derived from the issuer URL using standard OIDC paths rather
 * than fetching the discovery document from the browser, which would fail with
 * CORS errors when Dex runs on a different origin (e.g. Railway deployment).
 */

const trimSlash = (s: string) => s.replace(/\/+$/, '')

export const OIDC_ISSUER = trimSlash(import.meta.env.VITE_OIDC_ISSUER || 'http://localhost:5556/dex')
export const OIDC_CLIENT_ID = import.meta.env.VITE_OIDC_CLIENT_ID || 'open-cis-web'
export const OIDC_REDIRECT_URI = `${window.location.origin}/auth/callback`

export const OIDC_AUTH_ENDPOINT = `${OIDC_ISSUER}/auth`
export const OIDC_TOKEN_ENDPOINT = `${OIDC_ISSUER}/token`

interface TokenResponse {
  access_token: string
  id_token?: string
  token_type: string
  expires_in?: number
}

export function generateState(): string {
  const array = new Uint8Array(32)
  crypto.getRandomValues(array)
  return Array.from(array, (b) => b.toString(16).padStart(2, '0')).join('')
}

export async function exchangeCodeForToken(
  code: string,
  codeVerifier: string,
): Promise<string> {
  const body = new URLSearchParams({
    grant_type: 'authorization_code',
    code,
    redirect_uri: OIDC_REDIRECT_URI,
    client_id: OIDC_CLIENT_ID,
    code_verifier: codeVerifier,
  })

  // Proxy through the API backend to avoid CORS issues with Dex
  const API_URL = trimSlash(import.meta.env.VITE_API_URL || '')
  const response = await fetch(`${API_URL}/api/auth/token`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: body.toString(),
  })

  if (!response.ok) {
    const text = await response.text()
    throw new Error(`Token exchange failed: ${response.status} ${text}`)
  }

  const data = (await response.json()) as TokenResponse
  if (!data.access_token) {
    throw new Error('Token response missing access_token')
  }
  return data.access_token
}
