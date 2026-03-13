const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

type ApiErrorCode = 'validation_error' | 'not_found' | 'service_unavailable' | 'internal_error'

interface ApiErrorBody {
  error: ApiErrorCode
  message: string
  details?: Record<string, unknown>
}

export class ApiRequestError extends Error {
  code: ApiErrorCode
  status: number
  details?: Record<string, unknown>

  constructor(status: number, body: ApiErrorBody) {
    super(body.message)
    this.name = 'ApiRequestError'
    this.code = body.error
    this.status = status
    this.details = body.details
  }
}

interface RequestOptions extends RequestInit {
  params?: Record<string, string | number>
}

async function request<T>(endpoint: string, options: RequestOptions = {}): Promise<T> {
  const { params, ...fetchOptions } = options

  let url = `${API_URL}${endpoint}`
  if (params) {
    const searchParams = new URLSearchParams()
    Object.entries(params).forEach(([key, value]) => {
      searchParams.append(key, String(value))
    })
    url += `?${searchParams.toString()}`
  }

  const response = await fetch(url, {
    ...fetchOptions,
    headers: {
      'Content-Type': 'application/json',
      ...fetchOptions.headers,
    },
  })

  if (!response.ok) {
    const fallback: ApiErrorBody = {
      error: 'internal_error',
      message: `Request failed (HTTP ${response.status})`,
    }
    const raw = await response.json().catch(() => null)
    const body: ApiErrorBody =
      raw != null &&
      typeof raw === 'object' &&
      typeof raw.error === 'string' &&
      typeof raw.message === 'string'
        ? { error: raw.error, message: raw.message, details: raw.details }
        : raw != null && typeof raw === 'object' && typeof raw.detail === 'string'
          ? { error: fallback.error, message: raw.detail }
          : fallback
    throw new ApiRequestError(response.status, body)
  }

  // Handle 204 No Content responses
  if (response.status === 204) {
    return undefined as T
  }

  return response.json() as Promise<T>
}

export const api = {
  get: <T>(endpoint: string, params?: Record<string, string | number>) =>
    request<T>(endpoint, { method: 'GET', params }),

  post: <T>(endpoint: string, data: unknown) =>
    request<T>(endpoint, { method: 'POST', body: JSON.stringify(data) }),

  patch: <T>(endpoint: string, data: unknown) =>
    request<T>(endpoint, { method: 'PATCH', body: JSON.stringify(data) }),

  delete: (endpoint: string) =>
    request<void>(endpoint, { method: 'DELETE' }),
}
