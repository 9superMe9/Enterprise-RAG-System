<template>
  <div :class="['message-bubble', role]">
    <div class="bubble-avatar">
      <el-avatar
        :size="34"
        :icon="role === 'user' ? 'UserFilled' : 'MagicStick'"
        :style="{ background: role === 'user' ? '#1677ff' : '#52c41a' }"
      />
    </div>
    <div class="bubble-body">
      <div class="bubble-content">
        <div class="message-content" v-html="renderedContent"></div>
        <div v-if="isStreaming" class="streaming-cursor">|</div>
      </div>
      <!-- 引用来源 -->
      <div v-if="sources && sources.length && !isStreaming" class="bubble-sources">
        <el-collapse>
          <el-collapse-item>
            <template #title>
              <span style="font-size:12px;color:#8c8c8c;">📎 参考来源 ({{ sources.length }})</span>
            </template>
            <div
              v-for="(src, i) in sources"
              :key="i"
              class="source-item"
            >
              <span class="source-index">#{{ i + 1 }}</span>
              <span class="source-text">{{ src }}</span>
            </div>
          </el-collapse-item>
        </el-collapse>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { marked } from 'marked'

const props = withDefaults(defineProps<{
  role: 'user' | 'assistant'
  content: string
  sources?: string[]
  isStreaming?: boolean
}>(), {
  sources: () => [],
  isStreaming: false,
})

const renderedContent = computed(() => {
  if (props.role === 'user') {
    return escapeHtml(props.content)
  }
  return marked(props.content, { breaks: true }) as string
})

function escapeHtml(text: string): string {
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
}
</script>

<style scoped lang="scss">
.message-bubble {
  display: flex;
  gap: 12px;
  padding: 8px 0;

  &.user {
    flex-direction: row-reverse;
    .bubble-content {
      background: #e6f4ff;
      border-radius: 16px 4px 16px 16px;
    }
    .bubble-sources { display: none; }
  }

  &.assistant {
    .bubble-content {
      background: #ffffff;
      border: 1px solid #f0f0f0;
      border-radius: 4px 16px 16px 16px;
    }
  }
}

.bubble-avatar {
  flex-shrink: 0;
  padding-top: 2px;
}

.bubble-body {
  max-width: 75%;
  min-width: 0;
}

.bubble-content {
  padding: 12px 16px;
  font-size: 14px;
  line-height: 1.7;
  position: relative;
}

.streaming-cursor {
  display: inline;
  animation: blink 1s infinite;
  color: #1677ff;
  font-weight: bold;
}

@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0; }
}

.bubble-sources {
  margin-top: 6px;
  :deep(.el-collapse) {
    border: none;
    --el-collapse-header-bg-color: transparent;
    --el-collapse-content-bg-color: transparent;
  }
  :deep(.el-collapse-item__header) {
    border: none;
    height: 28px;
    line-height: 28px;
    font-size: 12px;
  }
  :deep(.el-collapse-item__wrap) {
    border: none;
  }
  :deep(.el-collapse-item__content) {
    padding: 4px 0 8px;
  }
}

.source-item {
  display: flex;
  gap: 8px;
  padding: 6px 0;
  font-size: 12px;
  color: #8c8c8c;
  .source-index {
    color: #1677ff;
    font-weight: 600;
    flex-shrink: 0;
  }
  .source-text {
    line-height: 1.5;
  }
}
</style>
