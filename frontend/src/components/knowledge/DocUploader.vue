<template>
  <div class="doc-uploader">
    <el-upload
      ref="uploadRef"
      :auto-upload="false"
      :on-change="handleChange"
      :file-list="fileList"
      drag
      multiple
      accept=".pdf,.docx,.doc,.txt"
    >
      <el-icon class="el-icon--upload" :size="40"><UploadFilled /></el-icon>
      <div class="el-upload__text">
        将文件拖到此处，或<em>点击上传</em>
      </div>
      <template #tip>
        <div class="el-upload__tip">
          支持 PDF、Word (.docx/.doc)、TXT 文件
        </div>
      </template>
    </el-upload>

    <div class="upload-actions" v-if="fileList.length">
      <el-button type="primary" @click="handleUpload" :loading="uploading">
        上传到知识库
      </el-button>
      <el-button @click="handleClear">清空列表</el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import type { UploadInstance, UploadFile } from 'element-plus'

const emit = defineEmits<{
  uploaded: []
}>()

const uploadRef = ref<UploadInstance>()
const fileList = ref<UploadFile[]>([])
const uploading = ref(false)

function handleChange(_file: UploadFile, files: UploadFile[]) {
  fileList.value = files
}

function handleClear() {
  uploadRef.value?.clearFiles()
  fileList.value = []
}

async function handleUpload() {
  if (!fileList.value.length) return
  uploading.value = true
  try {
    const rawFiles: File[] = []
    for (const f of fileList.value) {
      // 获取原始 File 对象
      if (f.raw) rawFiles.push(f.raw)
      else if (f.url) {
        // fallback: 从 blob URL 读取
        const resp = await fetch(f.url)
        const blob = await resp.blob()
        rawFiles.push(new File([blob], f.name))
      }
    }
    await uploadFiles(rawFiles)
    ElMessage.success(`成功上传 ${rawFiles.length} 个文件`)
    handleClear()
    emit('uploaded')
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '上传失败')
  } finally {
    uploading.value = false
  }
}

// 通过 provide 从父组件获取
import { inject } from 'vue'
const uploadFiles = inject<(files: File[]) => Promise<void>>('uploadFiles', async () => {})
</script>

<style scoped lang="scss">
.doc-uploader {
  margin-bottom: 24px;
}
.upload-actions {
  margin-top: 12px;
  display: flex;
  gap: 8px;
  justify-content: flex-end;
}
</style>
