import { request } from '../../shared/api/client'
import type { Attempt, Quiz } from '../quiz/api'

export interface Page<T> {
  items: T[]
  next_cursor: string | null
  total_count: number
}
export interface ReviewItem {
  quiz: Quiz
  status: 'NEEDS_REVIEW' | 'RESOLVED'
  latest_attempt_id: string
  first_wrong_at: string
  last_wrong_at: string
  last_reviewed_at: string | null
  wrong_attempts: number
  retryable: boolean
}
export interface CategoryStats {
  category: string
  total_attempts: number
  correct_attempts: number
  accuracy: number | null
}
export interface Stats {
  total_attempts: number
  correct_attempts: number
  accuracy: number | null
  unique_quizzes: number
  needs_review: number
  resolved_reviews: number
  by_category: CategoryStats[]
}
export const categoryLabels: Record<string, string> = {
  OPERATING_SYSTEM: '운영체제',
  NETWORK: '네트워크',
  DATABASE: '데이터베이스',
  DATA_STRUCTURE: '자료구조',
  ALGORITHM: '알고리즘',
  COMPUTER_ARCHITECTURE: '컴퓨터 구조',
}
export function percentage(value: number | null): string {
  return value === null
    ? '—'
    : `${(value * 100).toLocaleString('ko-KR', { maximumFractionDigits: 1 })}%`
}
export function timestamp(value: string): string {
  return new Date(value).toLocaleString('ko-KR')
}
export function query(filters: Record<string, string | null | undefined>): string {
  const params = new URLSearchParams()
  Object.entries(filters).forEach(([key, value]) => {
    if (value != null && value !== '') params.set(key, value)
  })
  return params.toString()
}
export const getStats = () => request<Stats>('/me/stats')
export const getAttempt = (id: string) => request<Attempt>(`/me/attempts/${encodeURIComponent(id)}`)
export const getHistory = (filters: Record<string, string | null | undefined>) =>
  request<Page<Attempt>>(`/me/attempts?${query(filters)}`)
export const getReviews = (filters: Record<string, string | null | undefined>) =>
  request<Page<ReviewItem>>(`/me/wrong-answers?${query(filters)}`)
