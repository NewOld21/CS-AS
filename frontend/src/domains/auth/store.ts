import { defineStore } from 'pinia'
import { ref } from 'vue'
import { ApiError, post, request, resetCsrf } from '../../shared/api/client'
export interface User {
  id: string
  email: string
  nickname: string | null
}
export const useAuth = defineStore('auth', () => {
  const user = ref<User | null>(null)
  const checked = ref(false)
  async function restore() {
    try {
      user.value = await request<User>('/auth/me')
    } catch (error) {
      user.value = null
      if (!(error instanceof ApiError && error.status === 401)) throw error
    } finally {
      checked.value = true
    }
  }
  async function login(email: string, password: string) {
    user.value = await post<User>('/auth/login', { email, password })
    resetCsrf()
    checked.value = true
  }
  async function signup(email: string, password: string, nickname: string) {
    return await post<User>('/auth/signup', { email, password, ...(nickname ? { nickname } : {}) })
  }
  async function logout() {
    try {
      await post('/auth/logout')
    } catch (error) {
      if (!(error instanceof ApiError && error.status === 401)) throw error
    }
    user.value = null
    resetCsrf()
    checked.value = true
  }
  return { user, checked, restore, login, signup, logout }
})
