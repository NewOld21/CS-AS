import { post, request } from '../../shared/api/client'

export interface Category {
  id: string
  name: string
  quiz_count: number
}
export interface QuizOption {
  id: string
  position: number
  text: string
}
export interface Quiz {
  id: string
  version: number
  stem: string
  category: string
  difficulty: string
  origin: string
  concept_ids: string[]
  options: QuizOption[]
}
export interface Source {
  source_id: string
  document_id: string
  revision: string
  chunk_id: string
  index_version: string
  title: string
  url: string
  locator: string
}
export interface Attempt {
  id: string
  quiz: Quiz
  selected_option_id: string
  correct_option_id: string
  is_correct: boolean
  explanation: string
  sources: Source[]
  submitted_at: string
}
export interface ChatSession {
  id: string
  quiz_id: string | null
  attempt_id: string | null
  created_at: string
}
export interface ChatAnswer {
  request_id: string
  message_id: string
  status: 'answered' | 'insufficient_evidence'
  answer: string | null
  sources: Source[]
  concept_ids: string[]
}

export const listCategories = () => request<Category[]>('/quiz/categories')
export const listQuizzes = (category: string) =>
  request<{ items: Quiz[]; next_cursor: string | null }>(
    `/quizzes?category=${encodeURIComponent(category)}&limit=20`,
  )
export const submitAttempt = (quizId: string, optionId: string) =>
  post<Attempt>(
    `/quizzes/${quizId}/attempts`,
    { selected_option_id: optionId },
    { 'Idempotency-Key': crypto.randomUUID() },
  )
export const createContextChat = (quizId: string, attemptId: string) =>
  post<ChatSession>('/chat/sessions', { quiz_id: quizId, attempt_id: attemptId })
export const ask = (sessionId: string, question: string) =>
  post<ChatAnswer>(`/chat/sessions/${sessionId}/messages`, { question })

export function safeSourceUrl(value: string): string | null {
  try {
    const url = new URL(value)
    return url.protocol === 'https:' ? url.href : null
  } catch {
    return null
  }
}
