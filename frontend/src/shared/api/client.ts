export class ApiError extends Error {
  constructor(
    public status: number,
    public code: string,
  ) {
    super(code)
  }
}
let csrf: string | null = null
export function resetCsrf() {
  csrf = null
}
export async function request<T>(
  path: string,
  init: RequestInit = {},
  timeoutMs = 12000,
): Promise<T> {
  const controller = new AbortController()
  const timeout = setTimeout(() => controller.abort(), timeoutMs)
  try {
    const response = await fetch(`/api/v1${path}`, {
      ...init,
      credentials: 'include',
      signal: controller.signal,
    })
    if (!response.ok) {
      const error = (await response.json().catch(() => ({}))) as { code?: string }
      throw new ApiError(response.status, error.code ?? 'REQUEST_FAILED')
    }
    return response.status === 204 ? (undefined as T) : ((await response.json()) as T)
  } catch (error) {
    if (error instanceof ApiError) throw error
    throw new ApiError(
      0,
      error instanceof DOMException && error.name === 'AbortError' ? 'TIMEOUT' : 'NETWORK_ERROR',
    )
  } finally {
    clearTimeout(timeout)
  }
}
export async function post<T>(
  path: string,
  body?: unknown,
  headers: Record<string, string> = {},
  timeoutMs = 12000,
): Promise<T> {
  if (!csrf) csrf = (await request<{ token: string }>('/auth/csrf')).token
  try {
    return await request<T>(
      path,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-CSRF-Token': csrf, ...headers },
        body: body === undefined ? undefined : JSON.stringify(body),
      },
      timeoutMs,
    )
  } catch (error) {
    if (error instanceof ApiError && (error.status === 401 || error.status === 403)) resetCsrf()
    // State-changing requests are never automatically replayed.
    throw error
  }
}
