import { describe, expect, it } from 'vitest'
import { percentage, query } from '../../src/domains/learning/api'

describe('learning display and filter contract', () => {
  it('distinguishes no attempts from zero accuracy and counts fractional accuracy', () => {
    expect(percentage(null)).toBe('—')
    expect(percentage(0)).toBe('0%')
    expect(percentage(1 / 3)).toBe('33.3%')
  })
  it('keeps false filters and escapes opaque cursor values', () => {
    expect(query({ correct: 'false', category: '', cursor: 'a+/=', origin: null })).toBe(
      'correct=false&cursor=a%2B%2F%3D',
    )
  })
})
