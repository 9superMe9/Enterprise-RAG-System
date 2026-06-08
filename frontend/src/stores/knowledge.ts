import { defineStore } from 'pinia'
import { ref } from 'vue'
import { getDocumentsApi, uploadDocumentsApi, deleteDocumentApi, type Document } from '@/api/knowledge'

export const useKnowledgeStore = defineStore('knowledge', () => {
  const documents = ref<Document[]>([])
  const totalChunks = ref(0)
  const totalDocuments = ref(0)
  const loading = ref(false)

  async function fetchDocuments() {
    loading.value = true
    try {
      const res = await getDocumentsApi()
      documents.value = res.data.documents
      totalChunks.value = res.data.total_chunks
      totalDocuments.value = res.data.total_documents
    } finally {
      loading.value = false
    }
  }

  async function uploadFiles(files: File[]) {
    await uploadDocumentsApi(files)
    await fetchDocuments()
  }

  async function deleteDocument(filename: string) {
    await deleteDocumentApi(filename)
    await fetchDocuments()
  }

  return { documents, totalChunks, totalDocuments, loading, fetchDocuments, uploadFiles, deleteDocument }
})
