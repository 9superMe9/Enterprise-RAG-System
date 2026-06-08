<template>
  <div class="app-layout">
    <AppSidebar />
    <div class="app-main">
      <AppHeader />
      <div class="main-content">
        <!-- 聊天区域 -->
        <div class="chat-area" ref="chatAreaRef">
          <!-- 欢迎界面 / 空状态 -->
          <WelcomeBubble
            v-if="!msgList.length && !streaming"
            @select="handleSend"
          />

          <!-- 消息列表 -->
          <div v-if="msgList.length" class="message-list">
            <MessageBubble
              v-for="msg in msgList"
              :key="msg.id"
              :role="msg.role as any"
              :content="msg.content"
              :sources="msg.sources_json ? JSON.parse(msg.sources_json) : []"
            />
            <!-- 流式消息 -->
            <MessageBubble
              v-if="streaming"
              role="assistant"
              :content="streamContent"
              :is-streaming="true"
            />
          </div>
          <div ref="bottomRef" />
        </div>

        <!-- 输入区域 -->
        <ChatInput :disabled="streaming" @send="handleSend" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, watch, nextTick, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import AppSidebar from '@/components/layout/AppSidebar.vue'
import AppHeader from '@/components/layout/AppHeader.vue'
import WelcomeBubble from '@/components/chat/WelcomeBubble.vue'
import MessageBubble from '@/components/chat/MessageBubble.vue'
import ChatInput from '@/components/chat/ChatInput.vue'
import { useChatStore } from '@/stores/chat'
import { chatStreamApi } from '@/api/chat'

interface LocalMessage {
  id: number
  role: 'user' | 'assistant'
  content: string
  sources_json: string
}

const route = useRoute()
const chatStore = useChatStore()

const msgList = reactive<LocalMessage[]>([])
const streaming = ref(false)
const streamContent = ref('')
const chatAreaRef = ref<HTMLElement>()
const bottomRef = ref<HTMLElement>()

// 监听路由变化，加载对应对话
watch(
  () => route.params.id,
  async (id) => {
    if (id) {
      await chatStore.selectConversation(Number(id))
      msgList.splice(0, msgList.length, ...chatStore.messages.map(m => ({
        id: m.id,
        role: m.role as 'user' | 'assistant',
        content: m.content,
        sources_json: m.sources_json,
      })))
    } else {
      msgList.splice(0, msgList.length)
    }
    scrollToBottom()
  },
  { immediate: true }
)

onMounted(async () => {
  if (route.params.id) {
    await chatStore.selectConversation(Number(route.params.id))
    msgList.splice(0, msgList.length, ...chatStore.messages.map(m => ({
      id: m.id,
      role: m.role as 'user' | 'assistant',
      content: m.content,
      sources_json: m.sources_json,
    })))
  }
  scrollToBottom()
})

function scrollToBottom() {
  nextTick(() => {
    bottomRef.value?.scrollIntoView({ behavior: 'smooth' })
  })
}

async function handleSend(text: string) {
  if (streaming.value) return

  // 添加用户消息到本地
  msgList.push({
    id: Date.now(),
    role: 'user',
    content: text,
    sources_json: '[]',
  })
  scrollToBottom()

  // 流式请求
  streaming.value = true
  streamContent.value = ''

  try {
    const response = await chatStreamApi({
      question: text,
      conversation_id: chatStore.currentConvId || undefined,
      model_name: chatStore.currentModel,
    })

    if (!response.ok) {
      const errData = await response.json().catch(() => ({ detail: '请求失败' }))
      throw new Error(errData.detail || '请求失败')
    }

    const reader = response.body?.getReader()
    if (!reader) throw new Error('无法读取响应流')

    const decoder = new TextDecoder()
    let buffer = ''
    let convId = chatStore.currentConvId
    let finalSources: string[] = []

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() || ''

      for (const line of lines) {
        if (!line.startsWith('data: ')) continue
        const jsonStr = line.slice(6)
        try {
          const data = JSON.parse(jsonStr)
          if (data.type === 'token') {
            streamContent.value += data.content
            scrollToBottom()
          } else if (data.type === 'done') {
            convId = data.conversation_id
            finalSources = data.sources || []
          } else if (data.type === 'error') {
            streamContent.value += `\n\n[错误: ${data.content}]`
          }
        } catch { /* ignore */ }
      }
    }

    // 保存 assistant 消息
    msgList.push({
      id: Date.now() + 1,
      role: 'assistant',
      content: streamContent.value,
      sources_json: JSON.stringify(finalSources),
    })

    // 更新对话ID
    if (convId && !chatStore.currentConvId) {
      chatStore.currentConvId = convId
    }

    // 刷新侧边栏
    await chatStore.fetchConversations()
  } catch (e: any) {
    ElMessage.error(e.message || '对话失败')
    msgList.push({
      id: Date.now() + 1,
      role: 'assistant',
      content: `抱歉，请求失败: ${e.message}`,
      sources_json: '[]',
    })
  } finally {
    streaming.value = false
    streamContent.value = ''
    scrollToBottom()
  }
}
</script>

<style scoped lang="scss">
.app-layout {
  display: flex;
  height: 100vh;
  overflow: hidden;
}

.app-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
  background: #f5f6f8;
}

.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.chat-area {
  flex: 1;
  overflow-y: auto;
  padding: 16px 24px;
}

.message-list {
  max-width: 900px;
  margin: 0 auto;
}
</style>
