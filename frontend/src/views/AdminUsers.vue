<template>
  <div class="app-layout">
    <AppSidebar />
    <div class="app-main">
      <AppHeader />
      <div class="main-content">
        <div class="admin-page">
          <div class="page-header">
            <h2>用户管理</h2>
          </div>

          <el-table :data="users" stripe v-loading="loading">
            <el-table-column prop="id" label="ID" width="80" />
            <el-table-column prop="username" label="用户名" min-width="150" />
            <el-table-column prop="role" label="角色" width="100">
              <template #default="{ row }">
                <el-tag :type="row.role === 'admin' ? 'danger' : 'info'" size="small">
                  {{ row.role }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="created_at" label="创建时间" width="180" />
            <el-table-column label="操作" width="100" align="center">
              <template #default="{ row }">
                <el-popconfirm
                  v-if="row.id !== authStore.user?.id"
                  title="确定删除该用户？将同时删除其所有对话"
                  @confirm="handleDelete(row.id)"
                >
                  <template #reference>
                    <el-button type="danger" link size="small">删除</el-button>
                  </template>
                </el-popconfirm>
                <span v-else style="color:#bfbfbf;font-size:12px;">当前用户</span>
              </template>
            </el-table-column>
            <template #empty>
              <div class="empty-state">暂无用户数据</div>
            </template>
          </el-table>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import AppSidebar from '@/components/layout/AppSidebar.vue'
import AppHeader from '@/components/layout/AppHeader.vue'
import { useAuthStore } from '@/stores/auth'
import { getUsersApi, deleteUserApi } from '@/api/knowledge'

const authStore = useAuthStore()
const users = ref<any[]>([])
const loading = ref(false)

onMounted(fetchUsers)

async function fetchUsers() {
  loading.value = true
  try {
    const res = await getUsersApi()
    users.value = res.data.users
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '获取用户列表失败')
  } finally {
    loading.value = false
  }
}

async function handleDelete(userId: number) {
  try {
    await deleteUserApi(userId)
    ElMessage.success('用户已删除')
    await fetchUsers()
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
.admin-page {
  max-width: 900px;
  margin: 0 auto;
}
.page-header {
  margin-bottom: 24px;
  h2 { margin: 0; font-size: 20px; font-weight: 700; color: #1f1f1f; }
}
.empty-state {
  text-align: center;
  padding: 40px 0;
  color: #bfbfbf;
}
</style>
