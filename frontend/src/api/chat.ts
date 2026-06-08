import request from './request'

export interface ChatParams {
  question: string
  conversation_id?: number
  model_name?: string
  top_k?: number
  stream?: boolean
}

export interface Conversation {
  id: number
  title: string
  model_name: string
  msg_count: number
  created_at: string
  updated_at: string
}

export interface Message {
  id: number
  role: 'user' | 'assistant' | 'system'
  content: string
  sources_json: string
  created_at: string
}

export function getModelsApi() {
  return request.get('/models')
}

export function getConversationsApi() {
  return request.get('/conversations')
}

export function createConversationApi(data: { title?: string; model_name?: string }) {
  return request.post('/conversations', data)
}

export function getConversationApi(id: number) {
  return request.get(`/conversations/${id}`)
}

export function updateConversationApi(id: number, data: { title?: string }) {
  return request.put(`/conversations/${id}`, data)
}

export function deleteConversationApi(id: number) {
  return request.delete(`/conversations/${id}`)
}

// 非流式聊天
export function chatApi(data: ChatParams) {
  return request.post('/chat', { ...data, stream: false })
}

// 流式聊天 - 返回 fetch Response 供 ReadableStream 读取
export function chatStreamApi(data: ChatParams, signal?: AbortSignal) {
  const authStore = useAuthStore()
  return fetch('/api/chat', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${authStore.token}`,
    },
    body: JSON.stringify({ ...data, stream: true }),
    signal,
  })
}

// 推荐问题
export function getSuggestionsApi() {
  return request.get('/suggestions')
}

// 内联导入避免循环依赖
import { useAuthStore } from '@/stores/auth'

