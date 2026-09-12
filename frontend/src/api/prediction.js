import request from '@/utils/request'

export function predictSingle(text) {
  return request.post('/predictions/single', { text })
}

export function predictBatch(data) {
  return request.post('/predictions/batch', data)
}

export function getBatchPredictionDetail(batchId, params) {
  return request.get(`/predictions/batch/${batchId}`, { params })
}

export function getPredictionHistory(params) {
  return request.get('/predictions/history', { params })
}

export function getPredictionCount(params) {
  return request.get('/predictions/history/count', { params })
}

export function getBatchPredictions(params) {
  return request.get('/predictions/batch/list', { params })
}

// -------- 用户反馈 --------

export function submitFeedback(data) {
  return request.post('/feedbacks', data)
}

export function getMyFeedback(predictionId) {
  return request.get(`/feedbacks/prediction/${predictionId}`)
}

// -------- 管理员反馈管理 --------

export function getFeedbackList(params) {
  return request.get('/feedbacks/list', { params })
}

export function getFeedbackCount(params) {
  return request.get('/feedbacks/list/count', { params })
}

export function getFeedbackStats() {
  return request.get('/feedbacks/stats')
}

export function startIncrementalTraining(data) {
  return request.post('/feedbacks/incremental-train', data)
}
