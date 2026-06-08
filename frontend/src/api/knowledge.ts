import request from './request'

export interface Document {
  name: string
  chunk_count: number
  source: string
}

export function getDocumentsApi() {
  return request.get('/documents')
}

export function uploadDocumentsApi(files: File[]) {
  const formData = new FormData()
  files.forEach((file) => formData.append('files', file))
  return request.post('/documents/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}

export function deleteDocumentApi(filename: string) {
  return request.delete(`/documents/${encodeURIComponent(filename)}`)
}

export function getUsersApi() {
  return request.get('/admin/users')
}

export function deleteUserApi(userId: number) {
  return request.delete(`/admin/users/${userId}`)
}
