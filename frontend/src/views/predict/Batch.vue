<template>
  <div class="batch-page">
    <div class="page-title-bar">
      <div>
        <h2>{{ userStore.isAdmin ? '批量预测' : '批量检测' }}</h2>
        <p class="page-desc">{{ userStore.isAdmin ? '选择数据集进行批量垃圾邮件分类，支持进度跟踪与结果统计' : '选择数据集对大量邮件进行批量智能分类' }}</p>
      </div>
    </div>

    <el-row :gutter="20">
      <!-- 左侧：配置与发起 -->
      <el-col :span="10">
        <div class="card">
          <h3 class="card-title">
            <el-icon><Setting /></el-icon>
            预测配置
          </h3>

          <el-form label-position="top">
            <el-form-item label="选择数据集">
              <el-select
                v-model="selectedDatasetId"
                placeholder="请选择数据集"
                style="width: 100%"
                filterable
                :loading="datasetsLoading"
              >
                <el-option
                  v-for="ds in datasets"
                  :key="ds.id"
                  :label="`${ds.name} (${ds.total_samples} 条)`"
                  :value="ds.id"
                />
              </el-select>
            </el-form-item>

            <div v-if="selectedDataset" class="dataset-brief">
              <div class="brief-item">
                <span class="brief-label">样本数</span>
                <span class="brief-value">{{ selectedDataset.total_samples }}</span>
              </div>
              <div class="brief-item">
                <span class="brief-label">格式</span>
                <el-tag size="small">{{ selectedDataset.file_format?.toUpperCase() }}</el-tag>
              </div>
              <div class="brief-item">
                <span class="brief-label">类型</span>
                <el-tag size="small" :type="selectedDataset.type === 'train' ? 'success' : 'info'">
                  {{ selectedDataset.type === 'train' ? '训练集' : '测试集' }}
                </el-tag>
              </div>
            </div>

            <el-button
              type="primary"
              class="start-btn"
              size="large"
              :loading="submitting"
              :disabled="!selectedDatasetId"
              @click="handleStartBatch"
            >
              <el-icon><VideoPlay /></el-icon>
              发起批量预测
            </el-button>
          </el-form>
        </div>

        <!-- 历史批量预测 -->
        <div class="card">
          <h3 class="card-title">
            <el-icon><Clock /></el-icon>
            历史批量预测
          </h3>
          <div v-if="batchHistory.length === 0" class="empty-history">
            <p>暂无历史记录</p>
          </div>
          <div
            v-for="b in batchHistory"
            :key="b.id"
            class="batch-history-item"
            :class="{ active: activeBatchId === b.id }"
            @click="selectBatch(b)"
          >
            <div class="bh-top">
              <span class="bh-id">#{{ b.id }}</span>
              <el-tag :type="statusType(b.status)" size="small">{{ statusText(b.status) }}</el-tag>
            </div>
            <div class="bh-bottom">
              <span>{{ b.total_count }} 条</span>
              <span>{{ formatDate(b.created_at) }}</span>
            </div>
          </div>
        </div>
      </el-col>

      <!-- 右侧：进度 & 结果 -->
      <el-col :span="14">
        <!-- 进度 -->
        <div class="card" v-if="activeBatch">
          <h3 class="card-title">
            <el-icon><Loading v-if="activeBatch.status === 'processing'" /><DataAnalysis v-else /></el-icon>
            {{ activeBatch.status === 'processing' ? '预测进度' : '预测结果' }}
            <el-tag :type="statusType(activeBatch.status)" size="small" style="margin-left: 8px">
              {{ statusText(activeBatch.status) }}
            </el-tag>
          </h3>

          <div class="progress-section" v-if="activeBatch.status === 'processing' || activeBatch.status === 'pending'">
            <el-progress
              type="dashboard"
              :percentage="Number(activeBatch.progress?.toFixed(1) || 0)"
              :width="180"
              :color="progressColors"
            >
              <template #default="{ percentage }">
                <div class="progress-inner">
                  <span class="progress-num">{{ percentage }}%</span>
                  <span class="progress-label">处理中</span>
                </div>
              </template>
            </el-progress>
            <p class="progress-hint">正在处理 {{ activeBatch.total_count }} 条数据，请稍候...</p>
          </div>

          <!-- 完成结果 -->
          <template v-if="activeBatch.status === 'completed'">
            <el-row :gutter="16" class="result-stats">
              <el-col :span="8">
                <div class="result-stat-item">
                  <span class="rs-value">{{ activeBatch.total_count }}</span>
                  <span class="rs-label">总数量</span>
                </div>
              </el-col>
              <el-col :span="8">
                <div class="result-stat-item spam">
                  <span class="rs-value">{{ activeBatch.spam_count }}</span>
                  <span class="rs-label">垃圾邮件</span>
                </div>
              </el-col>
              <el-col :span="8">
                <div class="result-stat-item ham">
                  <span class="rs-value">{{ activeBatch.ham_count }}</span>
                  <span class="rs-label">正常邮件</span>
                </div>
              </el-col>
            </el-row>

            <div class="time-info" v-if="activeBatch.processing_time">
              处理耗时：<strong>{{ activeBatch.processing_time.toFixed(2) }}s</strong>
            </div>

            <div class="chart-wrapper">
              <PieChart :data="batchPieData" title="分类结果分布" />
            </div>

            <!-- 详细结果列表 -->
            <div class="detail-section" v-if="batchDetail?.results?.length">
              <h4>预测明细（第 {{ detailPage }} 页）</h4>
              <el-table :data="batchDetail.results" size="small" stripe border max-height="400">
                <el-table-column type="index" label="#" width="55" align="center" />
                <el-table-column prop="input_text" label="邮件内容" min-width="250" show-overflow-tooltip />
                <el-table-column label="预测结果" width="100" align="center">
                  <template #default="{ row }">
                    <el-tag :type="row.prediction_label === 'spam' ? 'danger' : 'success'" size="small">
                      {{ row.prediction_label === 'spam' ? '垃圾' : '正常' }}
                    </el-tag>
                  </template>
                </el-table-column>
                <el-table-column label="置信度" width="100" align="center">
                  <template #default="{ row }">
                    {{ (row.confidence * 100).toFixed(1) }}%
                  </template>
                </el-table-column>
              </el-table>
              <div class="detail-pagination">
                <el-pagination
                  v-model:current-page="detailPage"
                  :page-size="detailPageSize"
                  :total="activeBatch.total_count"
                  layout="prev, pager, next"
                  small
                  @current-change="fetchBatchDetail"
                />
              </div>
            </div>
          </template>

          <!-- 失败 -->
          <div v-if="activeBatch.status === 'failed'" class="failed-section">
            <el-icon :size="48" color="#ef4444"><CircleCloseFilled /></el-icon>
            <p>批量预测失败，请检查数据集或联系管理员</p>
          </div>
        </div>

        <!-- 空状态 -->
        <div class="card empty-result" v-if="!activeBatch">
          <el-icon :size="64" color="#e5e7eb"><Files /></el-icon>
          <p>选择数据集并发起预测<br>或点击历史记录查看结果</p>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { getDatasets } from '@/api/dataset'
import {
  predictBatch, getBatchPredictionDetail, getBatchPredictions,
} from '@/api/prediction'
import { ElMessage } from 'element-plus'
import {
  Setting, VideoPlay, Clock, Loading, DataAnalysis,
  CircleCloseFilled, Files,
} from '@element-plus/icons-vue'
import { useUserStore } from '@/store/modules/user'
import PieChart from '@/components/charts/PieChart.vue'

const userStore = useUserStore()
const datasets = ref([])
const datasetsLoading = ref(false)
const selectedDatasetId = ref(null)
const submitting = ref(false)

const batchHistory = ref([])
const activeBatchId = ref(null)
const activeBatch = ref(null)
const batchDetail = ref(null)
const detailPage = ref(1)
const detailPageSize = 50

let pollTimer = null

const selectedDataset = computed(() =>
  datasets.value.find(d => d.id === selectedDatasetId.value) || null
)

const progressColors = [
  { color: '#6366f1', percentage: 30 },
  { color: '#3b82f6', percentage: 70 },
  { color: '#10b981', percentage: 100 },
]

const batchPieData = computed(() => {
  if (!activeBatch.value) return []
  return [
    { name: '垃圾邮件', value: activeBatch.value.spam_count || 0, itemStyle: { color: '#ef4444' } },
    { name: '正常邮件', value: activeBatch.value.ham_count || 0, itemStyle: { color: '#10b981' } },
  ]
})

function statusType(s) {
  const m = { pending: 'info', processing: 'warning', completed: 'success', failed: 'danger' }
  return m[s] || 'info'
}
function statusText(s) {
  const m = { pending: '等待中', processing: '处理中', completed: '已完成', failed: '失败' }
  return m[s] || s
}

function formatDate(dateStr) {
  if (!dateStr) return '--'
  const d = new Date(dateStr)
  return `${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')} ${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
}

async function fetchDatasets() {
  datasetsLoading.value = true
  try {
    const res = await getDatasets()
    datasets.value = res.data
  } catch {
    // silent
  } finally {
    datasetsLoading.value = false
  }
}

async function fetchBatchHistory() {
  try {
    const res = await getBatchPredictions({ page: 1, page_size: 20 })
    batchHistory.value = res.data
  } catch {
    // silent
  }
}

async function handleStartBatch() {
  if (!selectedDatasetId.value) return
  submitting.value = true
  try {
    const res = await predictBatch({ dataset_id: selectedDatasetId.value })
    const batch = res.data
    ElMessage.success(`批量预测已发起 (ID: ${batch.id})`)
    activeBatchId.value = batch.id
    activeBatch.value = batch
    fetchBatchHistory()
    startPolling(batch.id)
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || '发起批量预测失败')
  } finally {
    submitting.value = false
  }
}

function selectBatch(b) {
  stopPolling()
  activeBatchId.value = b.id
  activeBatch.value = { ...b }
  detailPage.value = 1

  if (b.status === 'completed') {
    fetchBatchDetail()
  } else if (b.status === 'processing' || b.status === 'pending') {
    startPolling(b.id)
  }
}

async function fetchBatchDetail() {
  if (!activeBatchId.value) return
  try {
    const res = await getBatchPredictionDetail(activeBatchId.value, {
      page: detailPage.value,
      page_size: detailPageSize,
    })
    activeBatch.value = res.data
    batchDetail.value = res.data
  } catch {
    ElMessage.error('获取预测详情失败')
  }
}

function startPolling(batchId) {
  stopPolling()
  pollTimer = setInterval(async () => {
    try {
      const res = await getBatchPredictionDetail(batchId, { page: 1, page_size: detailPageSize })
      activeBatch.value = res.data
      batchDetail.value = res.data

      if (res.data.status === 'completed' || res.data.status === 'failed') {
        stopPolling()
        fetchBatchHistory()
        if (res.data.status === 'completed') {
          ElMessage.success('批量预测已完成')
        }
      }
    } catch {
      // retry silently
    }
  }, 3000)
}

function stopPolling() {
  if (pollTimer) {
    clearInterval(pollTimer)
    pollTimer = null
  }
}

onMounted(() => {
  fetchDatasets()
  fetchBatchHistory()
})

onBeforeUnmount(() => {
  stopPolling()
})
</script>

<style scoped>
.batch-page {
  max-width: 1200px;
  margin: 0 auto;
}
.page-title-bar {
  margin-bottom: 20px;
}
.page-title-bar h2 {
  margin: 0 0 4px;
  font-size: 22px;
  font-weight: 700;
  color: #ffffff;
}
.page-desc {
  margin: 0;
  font-size: 14px;
  color: rgba(255, 255, 255, 0.4);
}

.card {
  background: rgba(255, 255, 255, 0.06);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
  margin-bottom: 16px;
}
.card-title {
  margin: 0 0 16px;
  font-size: 16px;
  font-weight: 600;
  color: #ffffff;
  display: flex;
  align-items: center;
  gap: 6px;
}

/* Dataset brief */
.dataset-brief {
  background: rgba(255, 255, 255, 0.04);
  border-radius: 10px;
  padding: 12px 16px;
  display: flex;
  gap: 24px;
  margin-bottom: 20px;
}
.brief-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.brief-label {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.4);
}
.brief-value {
  font-size: 14px;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.8);
}

.start-btn {
  width: 100%;
  border-radius: 10px;
  font-weight: 600;
  background: linear-gradient(135deg, #4f46e5, #7c3aed);
  border: none;
}
.start-btn:hover:not(:disabled) {
  background: linear-gradient(135deg, #4338ca, #6d28d9);
}

/* Batch history */
.empty-history {
  text-align: center;
  padding: 20px 0;
  color: rgba(255, 255, 255, 0.4);
}
.batch-history-item {
  padding: 10px 12px;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.15s;
  border: 1px solid transparent;
  margin-bottom: 6px;
}
.batch-history-item:hover {
  background: rgba(255, 255, 255, 0.04);
}
.batch-history-item.active {
  background: rgba(99, 102, 241, 0.12);
  border-color: rgba(99, 102, 241, 0.3);
}
.bh-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 4px;
}
.bh-id {
  font-weight: 600;
  color: rgba(255, 255, 255, 0.8);
  font-size: 14px;
}
.bh-bottom {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  color: rgba(255, 255, 255, 0.4);
}

/* Progress */
.progress-section {
  text-align: center;
  padding: 24px 0;
}
.progress-inner {
  display: flex;
  flex-direction: column;
  align-items: center;
}
.progress-num {
  font-size: 28px;
  font-weight: 700;
  color: #ffffff;
}
.progress-label {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.4);
}
.progress-hint {
  margin-top: 16px;
  font-size: 14px;
  color: rgba(255, 255, 255, 0.55);
}

/* Result stats */
.result-stats {
  margin-bottom: 16px;
}
.result-stat-item {
  background: rgba(255, 255, 255, 0.04);
  border-radius: 10px;
  padding: 16px;
  text-align: center;
}
.result-stat-item.spam { background: #fef2f2; }
.result-stat-item.ham { background: #f0fdf4; }
.rs-value {
  display: block;
  font-size: 24px;
  font-weight: 700;
  color: #ffffff;
}
.result-stat-item.spam .rs-value { color: #ef4444; }
.result-stat-item.ham .rs-value { color: #10b981; }
.rs-label {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.4);
  margin-top: 2px;
}

.time-info {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.55);
  margin-bottom: 16px;
}

.chart-wrapper {
  margin: 16px 0;
}

/* Detail section */
.detail-section h4 {
  margin: 0 0 12px;
  font-size: 15px;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.8);
}
.detail-pagination {
  display: flex;
  justify-content: center;
  margin-top: 12px;
}

/* Failed */
.failed-section {
  text-align: center;
  padding: 40px 0;
}
.failed-section p {
  color: rgba(255, 255, 255, 0.55);
  margin-top: 12px;
}

/* Empty result */
.empty-result {
  text-align: center;
  padding: 80px 0;
}
.empty-result p {
  color: rgba(255, 255, 255, 0.4);
  font-size: 14px;
  margin-top: 16px;
  line-height: 1.6;
}
</style>
