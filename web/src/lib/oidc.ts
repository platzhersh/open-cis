/**
 * OIDC configuration derived from environment variables.
 */

export const OIDC_ISSUER = import.meta.env.VITE_OIDC_ISSUER || 'http://localhost:5556/dex'
export const OIDC_CLIENT_ID = import.meta.env.VITE_OIDC_CLIENT_ID || 'open-cis-web'
export const OIDC_REDIRECT_URI = `${window.location.origin}/auth/callback`

interface OidcDiscovery {
  authorization_endpoint: string
  token_endpoint: string
  userinfo_endpoint: string
  jwks_uri: string
}

interface TokenResponse {
  access_token: string
  id_token?: string
  token_type: string
  expires_in?: number
}

let cachedDiscovery: OidcDiscovery | null = null

export async function getOidcDiscovery(): Promise<OidcDiscovery> {
  if (cachedDiscovery) return cachedDiscovery

  const response = await fetch(`${OIDC_ISSUER}/.well-known/openid-configuration`)
  if (!response.ok) {
    throw new Error(`Failed to fetch OIDC discovery: ${response.status}`)
  }
  cachedDiscovery = await response.json() as OidcDiscovery
  return cachedDiscovery
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
  const discovery = await getOidcDiscovery()

  const body = new URLSearchParams({
    grant_type: 'authorization_code',
    code,
    redirect_uri: OIDC_REDIRECT_URI,
    client_id: OIDC_CLIENT_ID,
    code_verifier: codeVerifier,
  })

  const response = await fetch(discovery.token_endpoint, {
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
