<template>
  <div class="welcome-bubble">
    <div class="welcome-icon">
      <el-icon :size="40" color="#1677ff"><MagicStick /></el-icon>
    </div>
    <div class="welcome-text">
      <h2>你好！我是企业知识助手 👋</h2>
      <p>基于 RAG 技术，我可以从你的企业知识库中检索信息并回答问题。</p>
    </div>
    <div class="suggestions" v-if="!loading && questions.length > 0">
      <div class="suggest-title">你可以试着问我：</div>
      <div
        v-for="q in questions"
        :key="q"
        class="suggest-item"
        @click="$emit('select', q)"
      >
        <el-icon><Pointer /></el-icon>
        <span>{{ q }}</span>
      </div>
    </div>
    <div class="suggestions" v-if="!loading && questions.length === 0">
      <div class="suggest-title">请输入你想了解的问题</div>
    </div>
    <div class="suggestions" v-if="loading">
      <div class="suggest-title">正在分析知识库...</div>
      <div class="suggest-item skeleton"></div>
      <div class="suggest-item skeleton"></div>
      <div class="suggest-item skeleton"></div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { getSuggestionsApi } from '@/api/chat'

defineEmits<{ select: [text: string] }>()

const questions = ref<string[]>([])
const loading = ref(true)

onMounted(async () => {
  try {
    const res = await getSuggestionsApi()
    questions.value = res.data.questions || []
  } catch {
    questions.value = []
  } finally {
    loading.value = false
  }
})
</script>

<style scoped lang="scss">
.welcome-bubble {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 48px 24px;
  text-align: center;
}

.welcome-icon {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  background: #e6f4ff;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 20px;
}

.welcome-text {
  h2 {
    margin: 0 0 8px;
    font-size: 22px;
    font-weight: 700;
    color: #1f1f1f;
  }
  p {
    margin: 0;
    color: #8c8c8c;
    font-size: 14px;
    line-height: 1.6;
  }
}

.suggestions {
  margin-top: 32px;
  width: 100%;
  max-width: 420px;
  .suggest-title {
    font-size: 13px;
    color: #8c8c8c;
    margin-bottom: 12px;
  }
  .suggest-item {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 10px 16px;
    background: #ffffff;
    border: 1px solid #e8e8e8;
    border-radius: 10px;
    margin-bottom: 8px;
    cursor: pointer;
    transition: all 0.15s;
    font-size: 14px;
    color: #434343;
    &:hover {
      border-color: #1677ff;
      color: #1677ff;
      background: #f0f5ff;
    }
  }
  .suggest-item.skeleton {
    height: 42px;
    background: #f0f0f0;
    border-color: #f0f0f0;
    cursor: default;
    animation: skeleton-pulse 1.5s ease-in-out infinite;
    &:hover {
      border-color: #f0f0f0;
      color: #434343;
      background: #f0f0f0;
    }
  }
}

@keyframes skeleton-pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.4; }
}
</style>
