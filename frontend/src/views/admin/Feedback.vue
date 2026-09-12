<template>
  <div class="feedback-page" :class="themeStore.isDark ? 'theme-dark' : 'theme-light'">
    <div class="page-title-bar">
      <div>
        <h2>反馈管理</h2>
        <p class="page-desc">查看用户对检测结果的反馈数据，并触发增量训练以提升模型精度</p>
      </div>
    </div>

    <!-- 统计卡片 -->
    <el-row :gutter="16" class="stats-row">
      <el-col :span="6">
        <div class="stat-card">
          <div class="stat-icon total-icon"><el-icon :size="24"><MessageBox /></el-icon></div>
          <div class="stat-body">
            <div class="stat-value">{{ stats.total ?? '-' }}</div>
            <div class="stat-label">总反馈数</div>
          </div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="stat-card">
          <div class="stat-icon correct-icon"><el-icon :size="24"><CircleCheckFilled /></el-icon></div>
          <div class="stat-body">
            <div class="stat-value">{{ stats.correct_count ?? '-' }}</div>
            <div class="stat-label">结果正确</div>
          </div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="stat-card">
          <div class="stat-icon wrong-icon"><el-icon :size="24"><CircleCloseFilled /></el-icon></div>
          <div class="stat-body">
            <div class="stat-value">{{ stats.wrong_count ?? '-' }}</div>
            <div class="stat-label">结果错误</div>
          </div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="stat-card">
          <div class="stat-icon rate-icon"><el-icon :size="24"><TrendCharts /></el-icon></div>
          <div class="stat-body">
            <div class="stat-value">
              {{ stats.accuracy_rate != null ? (stats.accuracy_rate * 100).toFixed(1) + '%' : '-' }}
            </div>
            <div class="stat-label">用户认可率</div>
          </div>
        </div>
      </el-col>
    </el-row>

    <el-row :gutter="20">
      <!-- 左侧：反馈列表 -->
      <el-col :span="15">
        <div class="card">
          <div class="card-header">
            <h3 class="card-title">
              <el-icon><List /></el-icon>
              反馈记录
            </h3>
            <div class="filter-bar">
              <el-radio-group v-model="filterCorrect" size="small" @change="fetchList">
                <el-radio-button :value="null">全部</el-radio-button>
                <el-radio-button :value="true">正确</el-radio-button>
                <el-radio-button :value="false">错误</el-radio-button>
              </el-radio-group>
            </div>
          </div>

          <el-table
            :data="feedbackList"
            v-loading="listLoading"
            stripe
            class="feedback-table"
            empty-text="暂无反馈数据"
          >
            <el-table-column label="ID" prop="id" width="60" />
            <el-table-column label="邮件内容" min-width="200">
              <template #default="{ row }">
                <span class="text-ellipsis">{{ row.input_text }}</span>
              </template>
            </el-table-column>
            <el-table-column label="模型判断" width="100">
              <template #default="{ row }">
                <el-tag :type="row.prediction_label === 'spam' ? 'danger' : 'success'" size="small">
                  {{ row.prediction_label === 'spam' ? '垃圾' : '正常' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="用户反馈" width="100">
              <template #default="{ row }">
                <el-tag :type="row.is_correct ? 'success' : 'danger'" size="small">
                  {{ row.is_correct ? '✓ 正确' : '✗ 错误' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="用户正确标签" width="110">
              <template #default="{ row }">
                <span v-if="!row.is_correct && row.correct_label">
                  <el-tag :type="row.correct_label === 'spam' ? 'danger' : 'success'" size="small" effect="plain">
                    {{ row.correct_label }}
                  </el-tag>
                </span>
                <span v-else class="text-muted">—</span>
              </template>
            </el-table-column>
            <el-table-column label="时间" width="160">
              <template #default="{ row }">
                <span class="text-muted">{{ formatDate(row.created_at) }}</span>
              </template>
            </el-table-column>
          </el-table>

          <div class="pagination-bar">
            <el-pagination
              v-model:current-page="page"
              :page-size="pageSize"
              :total="totalCount"
              layout="total, prev, pager, next"
              @current-change="fetchList"
              background
              small
            />
          </div>
        </div>
      </el-col>

      <!-- 右侧：增量训练配置 -->
      <el-col :span="9">
        <div class="card">
          <h3 class="card-title">
            <el-icon><Operation /></el-icon>
            增量训练
          </h3>

          <div class="train-hint" :class="canTrain ? 'hint-ready' : 'hint-warn'">
            <el-icon><InfoFilled /></el-icon>
            <span v-if="canTrain">
              当前有 <strong>{{ stats.wrong_count }}</strong> 条错误反馈，满足最小样本要求，可以触发增量训练。
            </span>
            <span v-else>
              错误反馈样本不足（当前 {{ stats.wrong_count ?? 0 }} 条，
              需至少 {{ trainConfig.min_feedback_samples }} 条）。
            </span>
          </div>

          <el-form :model="trainConfig" label-position="top" class="train-form">
            <el-form-item label="新模型名称" required>
              <el-input v-model="trainConfig.model_name" placeholder="例如: BERT-incremental-v1" />
            </el-form-item>
            <el-form-item label="基础数据集（原始训练集）" required>
              <el-select
                v-model="trainConfig.base_dataset_id"
                placeholder="选择原始训练数据集"
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

            <el-divider>超参数</el-divider>

            <el-row :gutter="12">
              <el-col :span="12">
                <el-form-item label="训练轮数">
                  <el-input-number v-model="trainConfig.epochs" :min="1" :max="10" style="width:100%" />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="批大小">
                  <el-input-number v-model="trainConfig.batch_size" :min="4" :max="64" :step="4" style="width:100%" />
                </el-form-item>
              </el-col>
            </el-row>
            <el-row :gutter="12">
              <el-col :span="12">
                <el-form-item label="学习率">
                  <el-input v-model="trainConfig.learning_rate" placeholder="2e-6" />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="反馈样本权重">
                  <el-input-number
                    v-model="trainConfig.feedback_sample_weight"
                    :min="1" :max="5" :step="0.5"
                    style="width:100%"
                  />
                </el-form-item>
              </el-col>
            </el-row>
            <el-form-item label="最小错误样本数门槛">
              <el-input-number
                v-model="trainConfig.min_feedback_samples"
                :min="1" :max="500"
                style="width:100%"
              />
            </el-form-item>

            <el-button
              type="primary"
              class="start-btn"
              size="large"
              :loading="trainSubmitting"
              :disabled="!canTrain || !trainConfig.model_name || !trainConfig.base_dataset_id"
              @click="handleStartTrain"
            >
              <el-icon><VideoPlay /></el-icon>
              开始增量训练
            </el-button>
          </el-form>
        </div>

        <!-- 训练进度 -->
        <div class="card progress-card" v-if="activeTraining">
          <h3 class="card-title">
            <el-icon class="spin-icon"><Loading /></el-icon>
            训练进度
          </h3>
          <div class="progress-section">
            <div class="progress-header">
              <span class="progress-label">{{ progressInfo.message || '准备中...' }}</span>
              <span class="progress-pct">{{ progressInfo.progress_pct || 0 }}%</span>
            </div>
            <el-progress
              :percentage="progressInfo.progress_pct || 0"
              :stroke-width="10"
              :color="progressGradient"
              :striped="progressInfo.phase !== 'done'"
              :striped-flow="progressInfo.phase === 'batch'"
            />
          </div>
          <div v-if="progressInfo.phase === 'done'" class="train-done">
            <el-icon color="#10b981" :size="20"><CircleCheckFilled /></el-icon>
            <span>训练完成！请前往「模型评估」对比后激活。</span>
          </div>
          <div v-if="progressInfo.phase === 'failed'" class="train-failed">
            <el-icon color="#ef4444" :size="20"><CircleCloseFilled /></el-icon>
            <span>训练失败，请查看日志。</span>
          </div>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useThemeStore } from '@/store/modules/theme'
import {
  getFeedbackList, getFeedbackCount, getFeedbackStats, startIncrementalTraining,
} from '@/api/prediction'
import { getDatasets } from '@/api/dataset'
import { getTrainingProgress } from '@/api/model'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  MessageBox, CircleCheckFilled, CircleCloseFilled, TrendCharts,
  List, Operation, InfoFilled, VideoPlay, Loading,
} from '@element-plus/icons-vue'

const themeStore = useThemeStore()

// ---- 统计 ----
const stats = ref({ total: 0, correct_count: 0, wrong_count: 0, accuracy_rate: 0, pending_train_count: 0 })

// ---- 列表 ----
const feedbackList = ref([])
const listLoading = ref(false)
const filterCorrect = ref(null)
const page = ref(1)
const pageSize = ref(15)
const totalCount = ref(0)

// ---- 数据集 ----
const datasets = ref([])
const datasetsLoading = ref(false)

// ---- 训练 ----
const trainConfig = ref({
  model_name: '',
  base_dataset_id: null,
  epochs: 3,
  batch_size: 16,
  learning_rate: 2e-6,
  feedback_sample_weight: 2.0,
  min_feedback_samples: 10,
})
const trainSubmitting = ref(false)
const activeTraining = ref(false)
const progressInfo = ref({})
const currentModelId = ref(null)
let pollTimer = null

const canTrain = computed(() =>
  (stats.value.wrong_count ?? 0) >= trainConfig.value.min_feedback_samples
)

const progressGradient = [
  { color: '#4f46e5', percentage: 0 },
  { color: '#7c3aed', percentage: 50 },
  { color: '#10b981', percentage: 100 },
]

// ---- 初始化 ----
onMounted(async () => {
  await Promise.all([fetchStats(), fetchList(), fetchDatasets()])
})

onUnmounted(() => {
  if (pollTimer) clearInterval(pollTimer)
})

async function fetchStats() {
  try {
    const res = await getFeedbackStats()
    stats.value = res.data
  } catch {
    // silent
  }
}

async function fetchList() {
  listLoading.value = true
  try {
    const params = {
      page: page.value,
      page_size: pageSize.value,
    }
    if (filterCorrect.value !== null) params.is_correct = filterCorrect.value

    const [listRes, countRes] = await Promise.all([
      getFeedbackList(params),
      getFeedbackCount(filterCorrect.value !== null ? { is_correct: filterCorrect.value } : {}),
    ])
    feedbackList.value = listRes.data
    totalCount.value = countRes.data.count
  } catch (err) {
    ElMessage.error('加载反馈列表失败')
  } finally {
    listLoading.value = false
  }
}

async function fetchDatasets() {
  datasetsLoading.value = true
  try {
    const res = await getDatasets({ page: 1, page_size: 100 })
    datasets.value = res.data
  } catch {
    // silent
  } finally {
    datasetsLoading.value = false
  }
}

async function handleStartTrain() {
  if (!trainConfig.value.model_name || !trainConfig.value.base_dataset_id) {
    ElMessage.warning('请填写模型名称并选择基础数据集')
    return
  }

  await ElMessageBox.confirm(
    `将使用 ${stats.value.wrong_count} 条错误反馈样本（权重 ×${trainConfig.value.feedback_sample_weight}）与原始数据集混合进行增量训练。此操作将在后台运行，不影响当前模型使用。是否继续？`,
    '确认增量训练',
    { type: 'warning', confirmButtonText: '开始训练', cancelButtonText: '取消' },
  ).catch(() => null)

  trainSubmitting.value = true
  try {
    const res = await startIncrementalTraining({
      ...trainConfig.value,
      learning_rate: parseFloat(trainConfig.value.learning_rate),
    })
    ElMessage.success(`增量训练已提交，模型ID: ${res.data.model_id}，使用了 ${res.data.feedback_samples_used} 条反馈样本`)
    currentModelId.value = res.data.model_id
    activeTraining.value = true
    progressInfo.value = { phase: 'queued', message: '任务已提交，准备中...', progress_pct: 0 }
    startPolling(res.data.model_id)
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || '提交训练任务失败')
  } finally {
    trainSubmitting.value = false
  }
}

function startPolling(modelId) {
  if (pollTimer) clearInterval(pollTimer)
  pollTimer = setInterval(async () => {
    try {
      const res = await getTrainingProgress(modelId)
      progressInfo.value = res.data
      if (res.data.status === 'completed' || res.data.status === 'failed') {
        clearInterval(pollTimer)
        pollTimer = null
        if (res.data.status === 'completed') {
          await fetchStats()
          await fetchList()
        }
      }
    } catch {
      clearInterval(pollTimer)
      pollTimer = null
    }
  }, 2000)
}

function formatDate(dateStr) {
  if (!dateStr) return '-'
  const d = new Date(dateStr)
  return d.toLocaleString('zh-CN', { hour12: false })
}
</script>

<style scoped>
/* ===== 布局 ===== */
.feedback-page {
  max-width: 1400px;
  margin: 0 auto;
}
.page-title-bar { margin-bottom: 20px; }
.page-title-bar h2 {
  margin: 0 0 4px;
  font-size: 22px;
  font-weight: 700;
}
.page-desc {
  margin: 0;
  font-size: 14px;
}

/* ===== 统计卡片 ===== */
.stats-row { margin-bottom: 20px; }
.stat-card {
  border-radius: 12px;
  padding: 16px 20px;
  display: flex;
  align-items: center;
  gap: 14px;
  border: 1px solid transparent;
}
.stat-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.total-icon { background: rgba(99, 102, 241, 0.15); color: #818cf8; }
.correct-icon { background: rgba(16, 185, 129, 0.15); color: #10b981; }
.wrong-icon { background: rgba(239, 68, 68, 0.15); color: #ef4444; }
.rate-icon { background: rgba(245, 158, 11, 0.15); color: #f59e0b; }
.stat-value {
  font-size: 24px;
  font-weight: 700;
  line-height: 1.2;
}
.stat-label {
  font-size: 12px;
  margin-top: 2px;
}

/* ===== 通用卡片 ===== */
.card {
  backdrop-filter: blur(20px);
  border-radius: 12px;
  padding: 24px;
  margin-bottom: 16px;
  border: 1px solid transparent;
}
.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}
.card-title {
  margin: 0 0 16px;
  font-size: 16px;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 6px;
}
.card-header .card-title { margin-bottom: 0; }

/* ===== 表格 ===== */
.text-ellipsis {
  display: block;
  max-width: 220px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 13px;
}
.text-muted { font-size: 13px; }
.pagination-bar {
  margin-top: 14px;
  display: flex;
  justify-content: flex-end;
}

/* ===== 训练提示 ===== */
.train-hint {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 10px 14px;
  border-radius: 8px;
  font-size: 13px;
  margin-bottom: 18px;
  line-height: 1.5;
}
.hint-ready {
  background: rgba(16, 185, 129, 0.1);
  border: 1px solid rgba(16, 185, 129, 0.25);
  color: #059669;
}
.hint-warn {
  background: rgba(245, 158, 11, 0.1);
  border: 1px solid rgba(245, 158, 11, 0.25);
  color: #d97706;
}

/* ===== 训练按钮 ===== */
.start-btn {
  width: 100%;
  margin-top: 8px;
  border-radius: 10px;
  font-weight: 600;
  background: linear-gradient(135deg, #4f46e5, #7c3aed);
  border: none;
}
.start-btn:hover:not(:disabled) {
  background: linear-gradient(135deg, #4338ca, #6d28d9);
}

/* ===== 训练进度 ===== */
.progress-card { margin-top: 0; }
.progress-section { margin-bottom: 12px; }
.progress-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
  font-size: 13px;
}
.progress-pct { font-weight: 700; color: #6366f1; }

.spin-icon { animation: spin 1.5s linear infinite; }
@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.train-done, .train-failed {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  padding: 8px 0 0;
}
.train-done { color: #10b981; }
.train-failed { color: #ef4444; }


/* ================================================
   深色主题
   ================================================ */
.theme-dark .page-title-bar h2 { color: #ffffff; }
.theme-dark .page-desc { color: rgba(255, 255, 255, 0.4); }

.theme-dark .stat-card {
  background: rgba(255, 255, 255, 0.06);
  border-color: rgba(255, 255, 255, 0.08);
}
.theme-dark .stat-value { color: #ffffff; }
.theme-dark .stat-label { color: rgba(255, 255, 255, 0.4); }

.theme-dark .card {
  background: rgba(255, 255, 255, 0.06);
  border-color: rgba(255, 255, 255, 0.08);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
}
.theme-dark .card-title { color: #ffffff; }

.theme-dark .feedback-table {
  --el-table-bg-color: transparent;
  --el-table-tr-bg-color: transparent;
  --el-table-row-hover-bg-color: rgba(255, 255, 255, 0.05);
  --el-table-border-color: rgba(255, 255, 255, 0.06);
  --el-table-header-bg-color: rgba(255, 255, 255, 0.04);
  --el-table-text-color: rgba(255, 255, 255, 0.75);
  --el-table-header-text-color: rgba(255, 255, 255, 0.45);
}
.theme-dark .text-ellipsis { color: rgba(255, 255, 255, 0.65); }
.theme-dark .text-muted { color: rgba(255, 255, 255, 0.3); }

.theme-dark .hint-ready { color: #6ee7b7; }
.theme-dark .hint-warn { color: #fcd34d; }

.theme-dark .progress-label { color: rgba(255, 255, 255, 0.65); }
.theme-dark .progress-pct { color: #a5b4fc; }

.theme-dark .train-form :deep(.el-form-item__label) {
  color: rgba(255, 255, 255, 0.65);
  font-size: 13px;
}
.theme-dark .train-form :deep(.el-input__wrapper),
.theme-dark .train-form :deep(.el-select .el-input__wrapper) {
  background: rgba(255, 255, 255, 0.06);
  border-color: rgba(255, 255, 255, 0.12);
  box-shadow: none;
}
.theme-dark .train-form :deep(.el-input__inner),
.theme-dark .train-form :deep(.el-select .el-input__inner) {
  color: rgba(255, 255, 255, 0.85);
}
.theme-dark .train-form :deep(.el-input-number__wrapper) {
  background: rgba(255, 255, 255, 0.06);
  border-color: rgba(255, 255, 255, 0.12);
}
.theme-dark .train-form :deep(.el-divider__text) {
  background: transparent;
  color: rgba(255, 255, 255, 0.3);
  font-size: 12px;
}
.theme-dark .filter-bar :deep(.el-radio-button__inner) {
  background: rgba(255, 255, 255, 0.05);
  border-color: rgba(255, 255, 255, 0.12);
  color: rgba(255, 255, 255, 0.55);
  font-size: 12px;
}
.theme-dark .filter-bar :deep(.el-radio-button__original-radio:checked + .el-radio-button__inner) {
  background: rgba(99, 102, 241, 0.3);
  border-color: rgba(99, 102, 241, 0.5);
  color: #a5b4fc;
  box-shadow: none;
}


/* ================================================
   浅色主题
   ================================================ */
.theme-light .page-title-bar h2 { color: #111827; }
.theme-light .page-desc { color: #6b7280; }

.theme-light .stat-card {
  background: #ffffff;
  border-color: #e5e7eb;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
}
.theme-light .stat-value { color: #111827; }
.theme-light .stat-label { color: #6b7280; }

.theme-light .card {
  background: #ffffff;
  border-color: #e5e7eb;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
}
.theme-light .card-title { color: #111827; }

.theme-light .feedback-table {
  --el-table-bg-color: #ffffff;
  --el-table-tr-bg-color: #ffffff;
  --el-table-row-hover-bg-color: #f9fafb;
  --el-table-border-color: #e5e7eb;
  --el-table-header-bg-color: #f3f4f6;
  --el-table-text-color: #374151;
  --el-table-header-text-color: #6b7280;
}
.theme-light .text-ellipsis { color: #374151; }
.theme-light .text-muted { color: #9ca3af; }

.theme-light .hint-ready { color: #059669; }
.theme-light .hint-warn { color: #d97706; }

.theme-light .progress-label { color: #6b7280; }
.theme-light .progress-pct { color: #4f46e5; }

.theme-light .train-form :deep(.el-form-item__label) {
  color: #374151;
  font-size: 13px;
}
.theme-light .train-form :deep(.el-divider__text) {
  background: #ffffff;
  color: #9ca3af;
  font-size: 12px;
}
.theme-light .filter-bar :deep(.el-radio-button__inner) {
  font-size: 12px;
}
</style>
