import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import {
  getConversationsApi, getConversationApi,
  createConversationApi, deleteConversationApi, updateConversationApi,
  getModelsApi,
  type Conversation, type Message,
} from '@/api/chat'

export const useChatStore = defineStore('chat', () => {
  const conversations = ref<Conversation[]>([])
  const currentConvId = ref<number | null>(null)
  const messages = ref<Message[]>([])
  const models = ref<{ label: string; model_name: string; provider: string }[]>([])
  const currentModel = ref<string>('qwen-turbo')
  const loading = ref(false)

  const currentConv = computed(() =>
    conversations.value.find((c) => c.id === currentConvId.value) || null
  )

  async function fetchConversations() {
    const res = await getConversationsApi()
    conversations.value = res.data.conversations
  }

  async function fetchModels() {
    try {
      const res = await getModelsApi()
      models.value = res.data.models
      if (models.value.length > 0 && !currentModel.value) {
        currentModel.value = models.value[0].model_name
      }
    } catch { /* ignore */ }
  }

  async function selectConversation(id: number) {
    currentConvId.value = id
    const res = await getConversationApi(id)
    messages.value = res.data.messages
  }

  async function newConversation() {
    const res = await createConversationApi({
      title: '新对话',
      model_name: currentModel.value,
    })
    currentConvId.value = res.data.id
    messages.value = []
    await fetchConversations()
  }

  async function deleteConversation(id: number) {
    await deleteConversationApi(id)
    if (currentConvId.value === id) {
      currentConvId.value = null
      messages.value = []
    }
    await fetchConversations()
  }

  async function renameConversation(id: number, title: string) {
    await updateConversationApi(id, { title })
    await fetchConversations()
  }

  function setModel(modelName: string) {
    currentModel.value = modelName
  }

  // 添加消息到本地列表
  function pushMessage(msg: Message) {
    messages.value.push(msg)
  }

  // 更新最后一条 assistant 消息内容（用于流式）
  function appendToLastAssistant(content: string) {
    const last = messages.value[messages.value.length - 1]
    if (last && last.role === 'assistant') {
      last.content += content
    }
  }

  function setLoading(val: boolean) {
    loading.value = val
  }

  return {
    conversations, currentConvId, messages, models, currentModel, loading, currentConv,
    fetchConversations, fetchModels,
    selectConversation, newConversation, deleteConversation, renameConversation,
    setModel, pushMessage, appendToLastAssistant, setLoading,
  }
})
