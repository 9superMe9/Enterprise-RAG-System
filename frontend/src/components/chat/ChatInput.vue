<template>
  <div class="chat-input">
    <el-input
      v-model="inputText"
      type="textarea"
      :rows="1"
      :autosize="{ minRows: 1, maxRows: 4 }"
      placeholder="输入你的问题，Enter 发送，Shift+Enter 换行..."
      resize="none"
      @keydown="handleKeydown"
      :disabled="disabled"
    />
    <el-button
      type="primary"
      :icon="Promotion"
      @click="handleSend"
      :disabled="!inputText.trim() || disabled"
      class="send-btn"
    >
      发送
    </el-button>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { Promotion } from '@element-plus/icons-vue'

const props = defineProps<{
  disabled?: boolean
}>()

const emit = defineEmits<{
  send: [text: string]
}>()

const inputText = ref('')

function handleKeydown(e: KeyboardEvent) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    handleSend()
  }
}

function handleSend() {
  const text = inputText.value.trim()
  if (!text || props.disabled) return
  emit('send', text)
  inputText.value = ''
}
</script>

<style scoped lang="scss">
.chat-input {
  display: flex;
  align-items: flex-end;
  gap: 10px;
  padding: 16px 24px;
  background: #ffffff;
  border-top: 1px solid #f0f0f0;

  :deep(.el-textarea__inner) {
    border-radius: 12px;
    font-size: 14px;
    background: #f5f6f8;
    border-color: #e8e8e8;
    &:focus {
      border-color: #1677ff;
      background: #ffffff;
    }
  }

  .send-btn {
    border-radius: 10px;
    flex-shrink: 0;
  }
}
</style>
