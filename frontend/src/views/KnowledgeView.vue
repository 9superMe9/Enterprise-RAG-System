<template>
  <div class="app-layout">
    <AppSidebar />
    <div class="app-main">
      <AppHeader />
      <div class="main-content">
        <div class="knowledge-page">
          <div class="page-header">
            <h2>知识库管理</h2>
            <p>管理企业文档，上传 PDF、Word、TXT 文件到知识库</p>
          </div>

          <!-- 统计卡片 -->
          <StatsCards
            :total-documents="knowledgeStore.totalDocuments"
            :total-chunks="knowledgeStore.totalChunks"
          />

          <!-- 上传区域 -->
          <DocUploader @uploaded="knowledgeStore.fetchDocuments()" />

          <!-- 文档列表 -->
          <DocTable
            :documents="knowledgeStore.documents"
            :loading="knowledgeStore.loading"
            @delete="handleDelete"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, provide } from 'vue'
import { ElMessage } from 'element-plus'
import AppSidebar from '@/components/layout/AppSidebar.vue'
import AppHeader from '@/components/layout/AppHeader.vue'
import StatsCards from '@/components/knowledge/StatsCards.vue'
import DocTable from '@/components/knowledge/DocTable.vue'
import DocUploader from '@/components/knowledge/DocUploader.vue'
import { useKnowledgeStore } from '@/stores/knowledge'

const knowledgeStore = useKnowledgeStore()

// 提供 uploadFiles 给子组件
provide('uploadFiles', async (files: File[]) => {
  await knowledgeStore.uploadFiles(files)
})

onMounted(() => {
  knowledgeStore.fetchDocuments()
})

async function handleDelete(filename: string) {
  try {
    await knowledgeStore.deleteDocument(filename)
    ElMessage.success(`已删除文档: ${filename}`)
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '删除失败')
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
  overflow-y: auto;
  padding: 24px;
}

.knowledge-page {
  max-width: 900px;
  margin: 0 auto;
}

.page-header {
  margin-bottom: 24px;
  h2 {
    margin: 0 0 4px;
    font-size: 20px;
    font-weight: 700;
    color: #1f1f1f;
  }
  p {
    margin: 0;
    color: #8c8c8c;
    font-size: 14px;
  }
}
</style>
