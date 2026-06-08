<template>
  <el-table :data="documents" stripe style="width: 100%" v-loading="loading">
    <el-table-column prop="name" label="文件名" min-width="200">
      <template #default="{ row }">
        <div class="doc-name">
          <el-icon color="#1677ff"><Document /></el-icon>
          <span>{{ row.name }}</span>
        </div>
      </template>
    </el-table-column>
    <el-table-column prop="chunk_count" label="知识块数" width="100" align="center" />
    <el-table-column label="操作" width="120" align="center">
      <template #default="{ row }">
        <el-popconfirm title="确定删除该文档？将移除所有关联的知识块" @confirm="$emit('delete', row.name)">
          <template #reference>
            <el-button type="danger" link size="small">删除</el-button>
          </template>
        </el-popconfirm>
      </template>
    </el-table-column>
    <template #empty>
      <div class="empty-state">
        <el-icon :size="48" color="#d9d9d9"><FolderOpened /></el-icon>
        <p>知识库暂无文档</p>
        <p class="empty-hint">请上传 PDF、Word 或 TXT 文件</p>
      </div>
    </template>
  </el-table>
</template>

<script setup lang="ts">
import type { Document } from '@/api/knowledge'

defineProps<{
  documents: Document[]
  loading?: boolean
}>()

defineEmits<{
  delete: [filename: string]
}>()
</script>

<style scoped lang="scss">
.doc-name {
  display: flex;
  align-items: center;
  gap: 8px;
}
.empty-state {
  text-align: center;
  padding: 40px 0;
  p {
    color: #8c8c8c;
    margin: 8px 0 0;
    font-size: 14px;
  }
  .empty-hint {
    font-size: 12px;
    color: #bfbfbf;
  }
}
</style>
