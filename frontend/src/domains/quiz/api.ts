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
  evidence_text?: string | null
  category?: string | null
  technology_version?: string | null
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
  title: string
  quiz_id: string | null
  attempt_id: string | null
  created_at: string
  updated_at: string
}
export interface ChatMessage {
  id: string
  role: 'USER' | 'ASSISTANT'
  content: string | null
  status: 'pending' | 'answered' | 'insufficient_evidence' | 'failed' | null
  created_at: string
  request_id: string | null
  concept_ids: string[]
  sources: Source[]
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
  post<ChatSession>('/chat/sessions', { title: null, quiz_id: quizId, attempt_id: attemptId })
export const createGeneralChat = (title?: string) =>
  post<ChatSession>('/chat/sessions', { title: title ?? null, quiz_id: null, attempt_id: null })
export const listChatSessions = (page = 0, limit = 20) =>
  request<{ items: ChatSession[]; next_page: number | null }>(
    `/chat/sessions?page=${page}&limit=${limit}`,
  )
export const getChatMessages = (sessionId: string, page = 0, limit = 50) =>
  request<{ items: ChatMessage[]; next_page: number | null }>(
    `/chat/sessions/${sessionId}/messages?page=${page}&limit=${limit}`,
  )
export const ask = (sessionId: string, question: string) =>
  post<ChatAnswer>(
    `/chat/sessions/${sessionId}/messages`,
    { question },
    { 'Idempotency-Key': crypto.randomUUID() },
  )

export function safeSourceUrl(value: string): string | null {
  try {
    const url = new URL(value)
    return url.protocol === 'https:' && !url.username && !url.password ? url.href : null
  } catch {
    return null
  }
}
