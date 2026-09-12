<template>
  <div class="admin-training-page">
    <div class="page-title-bar">
      <div>
        <h2>模型训练</h2>
        <p class="page-desc">配置训练参数，启动 BERT 模型微调训练任务</p>
      </div>
    </div>

    <el-row :gutter="20">
      <!-- 训练配置 -->
      <el-col :span="10">
        <div class="card">
          <h3 class="card-title">
            <el-icon><Setting /></el-icon>
            训练配置
          </h3>
          <el-form :model="config" label-position="top">
            <el-form-item label="模型名称" required>
              <el-input v-model="config.model_name" placeholder="例如: BERT-spam-v1" />
            </el-form-item>
            <el-form-item label="描述">
              <el-input v-model="config.description" type="textarea" :rows="2" />
            </el-form-item>
            <el-form-item label="训练数据集" required>
              <el-select v-model="config.dataset_id" placeholder="选择数据集" style="width: 100%" filterable :loading="datasetsLoading">
                <el-option v-for="ds in datasets" :key="ds.id" :label="`${ds.name} (${ds.total_samples} 条)`" :value="ds.id" />
              </el-select>
            </el-form-item>
            <el-form-item label="基础模型">
              <el-select v-model="config.base_model" style="width: 100%">
                <el-option label="bert-base-chinese" value="bert-base-chinese" />
                <el-option label="bert-base-uncased" value="bert-base-uncased" />
                <el-option label="distilbert-base-uncased" value="distilbert-base-uncased" />
              </el-select>
            </el-form-item>

            <el-divider>超参数</el-divider>

            <el-row :gutter="16">
              <el-col :span="12">
                <el-form-item label="训练轮数 (Epochs)">
                  <el-input-number v-model="config.epochs" :min="1" :max="50" style="width: 100%" />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="批大小 (Batch Size)">
                  <el-input-number v-model="config.batch_size" :min="4" :max="128" :step="4" style="width: 100%" />
                </el-form-item>
              </el-col>
            </el-row>
            <el-row :gutter="16">
              <el-col :span="12">
                <el-form-item label="学习率">
                  <el-input v-model="config.learning_rate" placeholder="2e-5" />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="最大序列长度">
                  <el-input-number v-model="config.max_seq_length" :min="32" :max="512" :step="32" style="width: 100%" />
                </el-form-item>
              </el-col>
            </el-row>
            <el-row :gutter="16">
              <el-col :span="12">
                <el-form-item label="冻结层数">
                  <el-input-number v-model="config.freeze_layers" :min="0" :max="12" style="width: 100%" />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="学习率衰减">
                  <el-select v-model="config.lr_decay_strategy" style="width: 100%">
                    <el-option label="线性 (Linear)" value="linear" />
                    <el-option label="余弦 (Cosine)" value="cosine" />
                    <el-option label="恒定 (Constant)" value="constant" />
                  </el-select>
                </el-form-item>
              </el-col>
            </el-row>

            <el-button type="primary" class="start-btn" size="large" :loading="submitting" :disabled="!config.model_name || !config.dataset_id" @click="handleStartTraining">
              <el-icon><VideoPlay /></el-icon>
              开始训练
            </el-button>
          </el-form>
        </div>
      </el-col>

      <!-- 右侧面板 -->
      <el-col :span="14">
        <!-- 实时训练进度 -->
        <div class="card progress-card" v-if="activeTraining">
          <h3 class="card-title">
            <el-icon class="spin-icon"><Loading /></el-icon>
            训练进度实时监控
          </h3>

          <!-- 设备信息 -->
          <div class="device-info" v-if="progressInfo.device_info">
            <el-tag :type="progressInfo.device_info.device === 'cuda' ? 'success' : 'info'" size="small">
              {{ progressInfo.device_info.device === 'cuda' ? 'GPU' : 'CPU' }}
            </el-tag>
            <span class="device-name">{{ progressInfo.device_info.device_name }}</span>
            <span class="device-detail" v-if="progressInfo.device_info.gpu_memory">
              | 显存: {{ progressInfo.device_info.gpu_memory }}
            </span>
            <span class="device-detail" v-if="progressInfo.device_info.cuda_version">
              | CUDA {{ progressInfo.device_info.cuda_version }}
            </span>
          </div>

          <!-- 类别权重 -->
          <div class="weight-info" v-if="progressInfo.class_weights">
            <el-tag type="warning" size="small">类别权重</el-tag>
            <span>ham: {{ progressInfo.class_weights.ham }}, spam: {{ progressInfo.class_weights.spam }}</span>
            <span class="weight-note">(自动计算，用于处理数据不平衡)</span>
          </div>

          <!-- 进度条 -->
          <div class="progress-section">
            <div class="progress-header">
              <span class="progress-label">{{ progressInfo.message || '准备中...' }}</span>
              <span class="progress-pct">{{ progressInfo.progress_pct || 0 }}%</span>
            </div>
            <el-progress
              :percentage="progressInfo.progress_pct || 0"
              :stroke-width="12"
              :color="progressGradient"
              :striped="progressInfo.phase !== 'done'"
              :striped-flow="progressInfo.phase === 'batch'"
            />
          </div>

          <!-- ETA -->
          <div class="eta-row" v-if="progressInfo.eta_seconds > 0">
            <el-icon><Timer /></el-icon>
            <span>预计剩余时间: <strong>{{ formatEta(progressInfo.eta_seconds) }}</strong></span>
            <span class="elapsed" v-if="progressInfo.elapsed_seconds">
              | 已用时: {{ formatEta(progressInfo.elapsed_seconds) }}
            </span>
          </div>

          <!-- Epoch 进度 -->
          <div class="epoch-detail" v-if="progressInfo.epoch">
            <span>Epoch {{ progressInfo.epoch }} / {{ progressInfo.total_epochs }}</span>
            <span v-if="progressInfo.batch"> | Batch {{ progressInfo.batch }} / {{ progressInfo.total_batches }}</span>
            <span v-if="progressInfo.train_loss"> | Loss: {{ progressInfo.train_loss.toFixed(4) }}</span>
            <span v-if="progressInfo.train_acc"> | Acc: {{ (progressInfo.train_acc * 100).toFixed(1) }}%</span>
          </div>
        </div>

        <!-- 模型列表 -->
        <div class="card">
          <h3 class="card-title">
            <el-icon><Cpu /></el-icon>
            训练任务列表
          </h3>
          <el-table :data="models" stripe border size="small" v-loading="modelsLoading">
            <el-table-column prop="id" label="ID" width="60" align="center" />
            <el-table-column prop="name" label="名称" min-width="140">
              <template #default="{ row }">
                <router-link :to="`/model/${row.id}`" class="model-link">{{ row.name }}</router-link>
              </template>
            </el-table-column>
            <el-table-column prop="base_model" label="基础模型" width="150" show-overflow-tooltip />
            <el-table-column label="状态" width="90" align="center">
              <template #default="{ row }">
                <el-tag :type="statusType(row.status)" size="small">{{ statusText(row.status) }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="准确率" width="90" align="center">
              <template #default="{ row }">
                {{ row.accuracy != null ? (row.accuracy * 100).toFixed(2) + '%' : '--' }}
              </template>
            </el-table-column>
            <el-table-column label="操作" width="140" align="center">
              <template #default="{ row }">
                <el-button v-if="row.status === 'completed' && !row.is_active" link type="success" size="small" @click="handleActivate(row)">激活</el-button>
                <el-tag v-if="row.is_active" type="success" size="small">已激活</el-tag>
                <el-button link type="danger" size="small" @click="handleDeleteModel(row)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { getDatasets } from '@/api/dataset'
import { getModels, startTraining, activateModel, deleteModel, getTrainingProgress } from '@/api/model'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Setting, VideoPlay, Cpu, Loading, Timer } from '@element-plus/icons-vue'

const datasetsLoading = ref(false)
const datasets = ref([])
const modelsLoading = ref(false)
const models = ref([])
const submitting = ref(false)

const activeTraining = ref(null)
const progressInfo = ref({})
let pollTimer = null

const config = ref({
  model_name: '',
  description: '',
  dataset_id: null,
  base_model: 'bert-base-chinese',
  epochs: 3,
  batch_size: 32,
  learning_rate: '2e-5',
  max_seq_length: 128,
  freeze_layers: 0,
  lr_decay_strategy: 'linear',
})

const progressGradient = [
  { color: '#6366f1', percentage: 20 },
  { color: '#8b5cf6', percentage: 50 },
  { color: '#10b981', percentage: 100 },
]

function statusType(s) {
  return { training: 'warning', completed: 'success', failed: 'danger' }[s] || 'info'
}
function statusText(s) {
  return { training: '训练中', completed: '已完成', failed: '失败' }[s] || s
}

function formatEta(seconds) {
  if (!seconds || seconds <= 0) return '--'
  if (seconds < 60) return `${Math.round(seconds)}秒`
  if (seconds < 3600) {
    const m = Math.floor(seconds / 60)
    const s = Math.round(seconds % 60)
    return `${m}分${s}秒`
  }
  const h = Math.floor(seconds / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  return `${h}小时${m}分`
}

async function fetchDatasets() {
  datasetsLoading.value = true
  try {
    const res = await getDatasets()
    datasets.value = res.data
  } catch { /* silent */ } finally {
    datasetsLoading.value = false
  }
}

async function fetchModels() {
  modelsLoading.value = true
  try {
    const res = await getModels()
    models.value = res.data
    const training = models.value.find(m => m.status === 'training')
    if (training && !activeTraining.value) {
      activeTraining.value = training.id
      startPolling(training.id)
    }
  } catch { /* silent */ } finally {
    modelsLoading.value = false
  }
}

function startPolling(modelId) {
  stopPolling()
  pollTimer = setInterval(async () => {
    try {
      const res = await getTrainingProgress(modelId)
      progressInfo.value = res.data
      if (res.data.status === 'completed') {
        ElMessage.success(res.data.message || '训练完成！')
        stopPolling()
        activeTraining.value = null
        progressInfo.value = {}
        fetchModels()
      } else if (res.data.status === 'failed') {
        ElMessage.error(res.data.message || '训练失败')
        stopPolling()
        activeTraining.value = null
        progressInfo.value = {}
        fetchModels()
      }
    } catch { /* silent */ }
  }, 2000)
}

function stopPolling() {
  if (pollTimer) {
    clearInterval(pollTimer)
    pollTimer = null
  }
}

async function handleStartTraining() {
  submitting.value = true
  try {
    const payload = {
      ...config.value,
      learning_rate: parseFloat(config.value.learning_rate),
    }
    const res = await startTraining(payload)
    ElMessage.success(res.data.message || '训练任务已提交')
    const modelId = res.data.model_id
    activeTraining.value = modelId
    progressInfo.value = { phase: 'queued', message: '任务已提交，正在初始化...', progress_pct: 0 }
    startPolling(modelId)
    fetchModels()
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || '提交训练任务失败')
  } finally {
    submitting.value = false
  }
}

async function handleActivate(row) {
  try {
    await activateModel(row.id)
    ElMessage.success('模型已激活')
    fetchModels()
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || '激活失败')
  }
}

async function handleDeleteModel(row) {
  await ElMessageBox.confirm(`确认删除模型「${row.name}」？`, '删除确认', { type: 'warning' })
  try {
    await deleteModel(row.id)
    ElMessage.success('删除成功')
    fetchModels()
  } catch {
    ElMessage.error('删除失败')
  }
}

onMounted(() => {
  fetchDatasets()
  fetchModels()
})

onUnmounted(() => {
  stopPolling()
})
</script>

<style scoped>
.admin-training-page {
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
  margin: 0 0 20px;
  font-size: 16px;
  font-weight: 600;
  color: #ffffff;
  display: flex;
  align-items: center;
  gap: 6px;
}
.start-btn {
  width: 100%;
  border-radius: 10px;
  font-weight: 600;
  background: linear-gradient(135deg, #4f46e5, #7c3aed);
  border: none;
  margin-top: 8px;
}
.model-link {
  color: #818cf8;
  text-decoration: none;
  font-weight: 500;
}
.model-link:hover {
  text-decoration: underline;
}

/* Progress card */
.progress-card {
  border: 2px solid rgba(99, 102, 241, 0.2);
  background: rgba(99, 102, 241, 0.08);
}
.progress-card .card-title {
  color: #818cf8;
}

.device-info {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 16px;
  padding: 10px 14px;
  background: rgba(255, 255, 255, 0.06);
  border-radius: 8px;
  font-size: 13px;
  color: rgba(255, 255, 255, 0.8);
}
.device-name {
  font-weight: 600;
}
.device-detail {
  color: rgba(255, 255, 255, 0.55);
}

.weight-info {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 16px;
  padding: 10px 14px;
  background: rgba(245, 158, 11, 0.1);
  border-radius: 8px;
  font-size: 13px;
  color: #fbbf24;
}
.weight-note {
  color: #f59e0b;
  font-size: 12px;
}

.progress-section {
  margin-bottom: 12px;
}
.progress-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}
.progress-label {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.65);
  font-weight: 500;
}
.progress-pct {
  font-size: 15px;
  font-weight: 700;
  color: #818cf8;
}

.eta-row {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: rgba(255, 255, 255, 0.55);
  margin-bottom: 8px;
}
.eta-row strong {
  color: rgba(255, 255, 255, 0.8);
}
.elapsed {
  color: rgba(255, 255, 255, 0.4);
}

.epoch-detail {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.55);
  padding: 8px 12px;
  background: rgba(255, 255, 255, 0.06);
  border-radius: 6px;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
.spin-icon {
  animation: spin 1.5s linear infinite;
}
</style>
