const API_PROXY_BASE = '/api/proxy'

type JsonRecord = Record<string, unknown>

function getFetchBase(): string {
  if (typeof window !== 'undefined') {
    return ''
  }

  const configured =
    process.env.FRANK_WEB_BASE ||
    process.env.NEXT_PUBLIC_APP_URL ||
    process.env.NEXT_PUBLIC_SITE_URL

  return (configured || 'http://127.0.0.1:3000').replace(/\/$/, '')
}

export async function parseJsonResponse(response: Response): Promise<JsonRecord> {
  const text = await response.text()
  if (!text) return {}
  try {
    return JSON.parse(text) as JsonRecord
  } catch {
    return { raw: text }
  }
}

export function getApiProxyUrl(path: string): string {
  const cleanPath = path.replace(/^\/+/, '')
  return `${API_PROXY_BASE}/${cleanPath}`
}

export function jsonHeaders(extra?: HeadersInit): HeadersInit {
  return {
    'Content-Type': 'application/json',
    ...(extra ?? {}),
  }
}

export function toApiError(response: Response, data: JsonRecord): Error {
  const detail =
    (typeof data.detail === 'string' && data.detail) ||
    (typeof data.message === 'string' && data.message) ||
    `API ${response.status} ${response.statusText}`

  return new Error(detail)
}

export async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const base = getFetchBase()
  const response = await fetch(`${base}${getApiProxyUrl(path)}`, {
    ...init,
    headers: jsonHeaders(init?.headers),
    cache: 'no-store',
  })

  const data = await parseJsonResponse(response)
  if (!response.ok) {
    throw toApiError(response, data)
  }

  return data as T
}
