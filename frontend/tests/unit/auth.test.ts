import { beforeEach, afterEach, describe, expect, it, vi } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import { validate, errorMessage } from '../../src/domains/auth/validation'
import { ApiError, post, resetCsrf } from '../../src/shared/api/client'
import { useAuth } from '../../src/domains/auth/store'

beforeEach(() => {
  resetCsrf()
  setActivePinia(createPinia())
})
afterEach(() => vi.unstubAllGlobals())
const json = (value: unknown, status = 200) =>
  new Response(JSON.stringify(value), { status, headers: { 'Content-Type': 'application/json' } })
describe('auth input and server policy', () => {
  it('accepts valid inputs without weakening password byte limits', () => {
    expect(validate('learner@example.com', 'correct-horse-battery', '탐험가')).toEqual({})
    expect(validate('learner@example.com', '가'.repeat(25)).password).toContain('72바이트')
    expect(validate('learner@example.com', 'a'.repeat(73)).password).toContain('72바이트')
  })
  it('rejects malformed email, short passwords and blank nickname', () => {
    expect(validate('learner@example.com', ' '.repeat(12))).toHaveProperty('password')
    expect(validate('wrong', 'short', '   ')).toHaveProperty('email')
    expect(validate('wrong', 'short', '   ')).toHaveProperty('password')
    expect(validate('wrong', 'short', '   ')).toHaveProperty('nickname')
  })
  it('maps safe error messages without echoing raw server messages', () => {
    expect(errorMessage(new ApiError(401, 'INVALID_CREDENTIALS'))).toContain('이메일 또는 비밀번호')
    expect(errorMessage(new ApiError(0, 'TIMEOUT'))).toContain('응답이 늦어지고')
  })
  it('gets a CSRF token and sends cookies, without automatic POST replay', async () => {
    const fetch = vi
      .fn()
      .mockResolvedValueOnce(json({ token: 'test-token' }))
      .mockResolvedValueOnce(json({ code: 'CSRF_INVALID' }, 403))
    vi.stubGlobal('fetch', fetch)
    await expect(
      post('/auth/login', { email: 'a@b.com', password: 'not-logged' }),
    ).rejects.toMatchObject({ status: 403 })
    expect(fetch).toHaveBeenCalledTimes(2)
    expect(fetch.mock.calls[1]![1]).toMatchObject({
      credentials: 'include',
      method: 'POST',
      headers: { 'X-CSRF-Token': 'test-token' },
    })
  })
  it('keeps signup separate from login', async () => {
    vi.stubGlobal(
      'fetch',
      vi
        .fn()
        .mockResolvedValueOnce(json({ token: 'test-token' }))
        .mockResolvedValueOnce(json({ id: 'id', email: 'a@b.com', nickname: null }, 201)),
    )
    const auth = useAuth()
    await auth.signup('a@b.com', 'correct-horse-battery', '')
    expect(auth.user).toBeNull()
  })
  it('refreshes CSRF after login before logout and clears only confirmed sessions', async () => {
    const fetch = vi
      .fn()
      .mockResolvedValueOnce(json({ token: 'before' }))
      .mockResolvedValueOnce(json({ id: 'id', email: 'a@b.com', nickname: null }))
      .mockResolvedValueOnce(json({ token: 'after' }))
      .mockResolvedValueOnce(new Response(null, { status: 204 }))
    vi.stubGlobal('fetch', fetch)
    const auth = useAuth()
    await auth.login('a@b.com', 'correct-horse-battery')
    expect(auth.user?.id).toBe('id')
    await auth.logout()
    expect(fetch.mock.calls[3]![1].headers['X-CSRF-Token']).toBe('after')
    expect(auth.user).toBeNull()
  })
  it('preserves login state when logout fails due to network', async () => {
    const auth = useAuth()
    auth.user = { id: 'id', email: 'a@b.com', nickname: null }
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new TypeError('offline')))
    await expect(auth.logout()).rejects.toMatchObject({ code: 'NETWORK_ERROR' })
    expect(auth.user?.id).toBe('id')
  })
  it('distinguishes unavailable service from an expired session', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValueOnce(json({ code: 'AUTH_REQUIRED' }, 401)))
    const auth = useAuth()
    await auth.restore()
    expect(auth.user).toBeNull()
    expect(auth.checked).toBe(true)
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new TypeError('offline')))
    await expect(auth.restore()).rejects.toMatchObject({ code: 'NETWORK_ERROR' })
  })
})
