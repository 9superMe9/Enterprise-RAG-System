import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { loginApi, registerApi, getMeApi } from '@/api/auth'

export interface UserInfo {
  id: number
  username: string
  role: string
}

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string>(localStorage.getItem('token') || '')
  const user = ref<UserInfo | null>(null)

  const isLoggedIn = computed(() => !!token.value)
  const isAdmin = computed(() => user.value?.role === 'admin')

  async function login(username: string, password: string) {
    const res = await loginApi({ username, password })
    token.value = res.data.token
    user.value = res.data.user
    localStorage.setItem('token', res.data.token)
  }

  async function register(username: string, password: string) {
    const res = await registerApi({ username, password })
    return res.data
  }

  async function fetchMe() {
    if (!token.value) return
    try {
      const res = await getMeApi()
      user.value = res.data
    } catch {
      logout()
    }
  }

  function logout() {
    token.value = ''
    user.value = null
    localStorage.removeItem('token')
  }

  return { token, user, isLoggedIn, isAdmin, login, register, fetchMe, logout }
})
