import request from '@/utils/request'

export function getOverview() {
  return request.get('/analysis/overview')
}

export function getPredictionTrend(days = 30) {
  return request.get('/analysis/prediction-trend', { params: { days } })
}

export function getModelComparison() {
  return request.get('/analysis/model-comparison')
}

export function getConfidenceDistribution() {
  return request.get('/analysis/confidence-distribution')
}
