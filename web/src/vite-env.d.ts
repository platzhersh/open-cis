/// <reference types="vite/client" />

declare const __APP_VERSION__: string

interface ImportMetaEnv {
  readonly VITE_API_URL?: string
  readonly VITE_OIDC_ISSUER?: string
  readonly VITE_OIDC_CLIENT_ID?: string
  readonly VITE_APP_MODE?: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
