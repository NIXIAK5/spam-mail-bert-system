import request from '@/utils/request'

export function getModels(params) {
  return request.get('/models/', { params })
}

export function getModel(id) {
  return request.get(`/models/${id}`)
}

export function getTrainingLogs(modelId) {
  return request.get(`/models/${modelId}/logs`)
}

export function getModelEvaluation(modelId) {
  return request.get(`/models/${modelId}/evaluation`)
}

export function getModelDetailedEvaluation(modelId) {
  return request.get(`/models/${modelId}/detailed-evaluation`)
}

export function startTraining(config) {
  return request.post('/models/train', config)
}


export function getTrainingProgress(modelId) {
  return request.get(`/models/${modelId}/progress`)
}

export function activateModel(modelId) {
  return request.post(`/models/${modelId}/activate`)
}

export function exportModel(data) {
  return request.post('/models/export', data)
}

export function downloadModel(modelId, format = 'pytorch') {
  return request.get(`/models/export/${modelId}/download`, {
    params: { format },
    responseType: 'blob',
  })
}

export function deleteModel(modelId) {
  return request.delete(`/models/${modelId}`)
}
