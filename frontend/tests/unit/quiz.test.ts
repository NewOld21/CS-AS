import { afterEach, describe, expect, it, vi } from 'vitest'
import { safeSourceUrl, submitAttempt } from '../../src/domains/quiz/api'
import { resetCsrf } from '../../src/shared/api/client'

afterEach(() => {
  vi.unstubAllGlobals()
  resetCsrf()
})

describe('quiz and citation client policy', () => {
  it('allows only HTTPS citation links', () => {
    expect(safeSourceUrl('https://example.org/docs/index')).toBe('https://example.org/docs/index')
    expect(safeSourceUrl('javascript:alert(1)')).toBeNull()
    expect(safeSourceUrl('http://example.org/insecure')).toBeNull()
    expect(safeSourceUrl('not a url')).toBeNull()
  })

  it('submits a fresh idempotency key without sending a correct answer', async () => {
    const fetch = vi
      .fn()
      .mockResolvedValueOnce(new Response(JSON.stringify({ token: 'csrf' }), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify({ id: 'attempt' }), { status: 200 }))
    vi.stubGlobal('fetch', fetch)
    vi.stubGlobal('crypto', { randomUUID: () => '00000000-0000-4000-8000-000000000001' })
    await submitAttempt('quiz-1', 'option-2')
    const init = fetch.mock.calls[1]![1] as RequestInit
    expect(init.headers).toMatchObject({
      'Idempotency-Key': '00000000-0000-4000-8000-000000000001',
      'X-CSRF-Token': 'csrf',
    })
    expect(init.body).toBe(JSON.stringify({ selected_option_id: 'option-2' }))
  })
})
