<template>
  <div class="stats-cards">
    <div class="stat-card">
      <div class="stat-value">{{ totalDocuments }}</div>
      <div class="stat-label">文档数量</div>
    </div>
    <div class="stat-card">
      <div class="stat-value">{{ totalChunks }}</div>
      <div class="stat-label">知识块数</div>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  totalDocuments: number
  totalChunks: number
}>()
</script>

<style scoped lang="scss">
.stats-cards {
  display: flex;
  gap: 16px;
  margin-bottom: 20px;
}

.stat-card {
  flex: 1;
  background: #ffffff;
  border: 1px solid #e8e8e8;
  border-radius: 12px;
  padding: 20px 24px;
  .stat-value {
    font-size: 32px;
    font-weight: 700;
    color: #1677ff;
  }
  .stat-label {
    font-size: 13px;
    color: #8c8c8c;
    margin-top: 4px;
  }
}
</style>
