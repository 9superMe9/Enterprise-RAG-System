<template>
  <div class="app-sidebar">
    <!-- Logo -->
    <div class="sidebar-logo">
      <el-icon :size="28" color="#1677ff"><MagicStick /></el-icon>
      <span class="logo-text">企业知识库</span>
    </div>

    <!-- 新建对话 -->
    <div class="sidebar-new-chat">
      <el-button type="primary" @click="handleNewChat" :icon="Plus" block>
        新建对话
      </el-button>
    </div>

    <!-- 导航菜单 -->
    <el-menu
      :default-active="activeMenu"
      :router="true"
      class="sidebar-menu"
      background-color="transparent"
    >
      <el-menu-item index="/chat">
        <el-icon><ChatDotRound /></el-icon>
        <span>对话</span>
      </el-menu-item>
      <el-menu-item index="/knowledge">
        <el-icon><FolderOpened /></el-icon>
        <span>知识库管理</span>
      </el-menu-item>
      <el-menu-item v-if="authStore.isAdmin" index="/admin/users">
        <el-icon><UserFilled /></el-icon>
        <span>用户管理</span>
      </el-menu-item>
    </el-menu>

    <!-- 对话历史 -->
    <div class="sidebar-conversations">
      <div class="conv-header">
        <span>对话历史</span>
      </div>
      <div class="conv-list" v-if="chatStore.conversations.length">
        <div
          v-for="conv in chatStore.conversations"
          :key="conv.id"
          :class="['conv-item', { active: chatStore.currentConvId === conv.id }]"
          @click="handleSelectConv(conv.id)"
        >
          <div class="conv-title text-ellipsis">{{ conv.title }}</div>
          <div class="conv-actions">
            <el-popconfirm
              title="确定删除该对话？"
              @confirm="handleDeleteConv(conv.id)"
            >
              <template #reference>
                <el-icon :size="14" class="conv-delete" @click.stop><Delete /></el-icon>
              </template>
            </el-popconfirm>
          </div>
        </div>
      </div>
      <div v-else class="conv-empty">
        <span>暂无对话记录</span>
      </div>
    </div>

    <!-- 底部模型选择 -->
    <div class="sidebar-model">
      <span class="model-label">当前模型</span>
      <el-select
        v-model="chatStore.currentModel"
        @change="handleModelChange"
        size="small"
        class="model-select"
      >
        <el-option
          v-for="m in chatStore.models"
          :key="m.model_name"
          :label="m.label"
          :value="m.model_name"
        />
      </el-select>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Plus } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '@/stores/auth'
import { useChatStore } from '@/stores/chat'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const chatStore = useChatStore()

const activeMenu = computed(() => {
  if (route.path.startsWith('/knowledge')) return '/knowledge'
  if (route.path.startsWith('/admin')) return '/admin/users'
  return '/chat'
})

onMounted(async () => {
  await chatStore.fetchModels()
  await chatStore.fetchConversations()
})

async function handleNewChat() {
  await chatStore.newConversation()
  router.push('/chat')
}

async function handleSelectConv(id: number) {
  await chatStore.selectConversation(id)
  router.push(`/chat/${id}`)
}

async function handleDeleteConv(id: number) {
  await chatStore.deleteConversation(id)
}

function handleModelChange(modelName: string) {
  chatStore.setModel(modelName)
}
</script>

<style scoped lang="scss">
.app-sidebar {
  width: 260px;
  height: 100vh;
  background: #ffffff;
  border-right: 1px solid #e8e8e8;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  user-select: none;
}

.sidebar-logo {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 20px 16px 12px;
  .logo-text {
    font-size: 18px;
    font-weight: 700;
    color: #1f1f1f;
  }
}

.sidebar-new-chat {
  padding: 0 16px 12px;
  :deep(.el-button) {
    border-radius: 8px;
    font-weight: 500;
  }
}

.sidebar-menu {
  border-right: none !important;
  padding: 0 8px;
  :deep(.el-menu-item) {
    height: 40px;
    line-height: 40px;
    border-radius: 8px;
    margin-bottom: 2px;
    color: #595959;
    &:hover {
      background: #f0f5ff;
      color: #1677ff;
    }
    &.is-active {
      background: #e6f4ff;
      color: #1677ff;
      font-weight: 600;
    }
  }
}

.sidebar-conversations {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  padding: 0 12px;
  .conv-header {
    padding: 12px 4px 8px;
    font-size: 12px;
    color: #8c8c8c;
    font-weight: 500;
    text-transform: uppercase;
    letter-spacing: 1px;
  }
  .conv-list {
    flex: 1;
    overflow-y: auto;
    padding-right: 4px;
  }
  .conv-item {
    padding: 10px 12px;
    border-radius: 8px;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 2px;
    transition: all 0.15s;
    &:hover {
      background: #f5f5f5;
      .conv-actions { opacity: 1; }
    }
    &.active {
      background: #e6f4ff;
      .conv-title { color: #1677ff; font-weight: 500; }
    }
  }
  .conv-title {
    flex: 1;
    font-size: 13px;
    color: #434343;
  }
  .conv-actions {
    opacity: 0;
    transition: opacity 0.15s;
    .conv-delete {
      color: #bfbfbf;
      cursor: pointer;
      &:hover { color: #ff4d4f; }
    }
  }
  .conv-empty {
    text-align: center;
    color: #bfbfbf;
    font-size: 13px;
    padding-top: 24px;
  }
}

.sidebar-model {
  padding: 12px 16px;
  border-top: 1px solid #f0f0f0;
  .model-label {
    font-size: 12px;
    color: #8c8c8c;
    display: block;
    margin-bottom: 6px;
  }
  .model-select {
    width: 100%;
  }
}
</style>
