/**
 * OIDC configuration derived from environment variables.
 */

export const OIDC_ISSUER = import.meta.env.VITE_OIDC_ISSUER || 'http://localhost:5556/dex'
export const OIDC_CLIENT_ID = import.meta.env.VITE_OIDC_CLIENT_ID || 'open-cis-web'
export const OIDC_REDIRECT_URI = `${window.location.origin}/auth/callback`
export const OIDC_CLIENT_SECRET = 'open-cis-secret'

interface OidcDiscovery {
  authorization_endpoint: string
  token_endpoint: string
  userinfo_endpoint: string
  jwks_uri: string
}

let cachedDiscovery: OidcDiscovery | null = null

export async function getOidcDiscovery(): Promise<OidcDiscovery> {
  if (cachedDiscovery) return cachedDiscovery

  const response = await fetch(`${OIDC_ISSUER}/.well-known/openid-configuration`)
  if (!response.ok) {
    throw new Error(`Failed to fetch OIDC discovery: ${response.status}`)
  }
  cachedDiscovery = await response.json()
  return cachedDiscovery!
}

export async function exchangeCodeForToken(code: string, codeVerifier: string): Promise<string> {
  const discovery = await getOidcDiscovery()

  const body = new URLSearchParams({
    grant_type: 'authorization_code',
    code,
    redirect_uri: OIDC_REDIRECT_URI,
    client_id: OIDC_CLIENT_ID,
    client_secret: OIDC_CLIENT_SECRET,
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

  const data = await response.json()
  return data.id_token || data.access_token
}
