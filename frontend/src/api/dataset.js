import request from '@/utils/request'

export function uploadDataset(formData) {
  return request.post('/datasets/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}

export function getDatasets(params) {
  return request.get('/datasets/', { params })
}

export function getDataset(id) {
  return request.get(`/datasets/${id}`)
}

export function previewDataset(id, rows = 10) {
  return request.get(`/datasets/${id}/preview`, { params: { rows } })
}

export function getDatasetStats(id) {
  return request.get(`/datasets/${id}/stats`)
}

export function cleanDataset(id, options = {}) {
  return request.post(`/datasets/${id}/clean`, options)
}

export function deleteDataset(id) {
  return request.delete(`/datasets/${id}`)
}
