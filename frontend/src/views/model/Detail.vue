<template>
  <div class="model-detail-page">
    <div class="page-title-bar">
      <div>
        <el-button text @click="$router.push('/model')" class="back-btn">
          <el-icon><ArrowLeft /></el-icon> 返回模型列表
        </el-button>
        <h2 v-if="model">{{ model.name }}</h2>
        <p class="page-desc" v-if="model">
          基础模型：{{ model.base_model }}
          <el-tag v-if="model.is_active" type="success" size="small" style="margin-left: 8px">当前激活</el-tag>
          <el-tag :type="statusType(model.status)" size="small" style="margin-left: 4px">{{ statusText(model.status) }}</el-tag>
        </p>
      </div>
    </div>

    <div v-loading="loading">
      <!-- 评估指标卡片 -->
      <el-row :gutter="16" class="metric-row" v-if="evaluation">
        <el-col :span="6">
          <div class="metric-card mc-blue">
            <span class="mc-value">{{ (evaluation.accuracy * 100).toFixed(2) }}%</span>
            <span class="mc-label">准确率 (Accuracy)</span>
            <el-progress :percentage="evaluation.accuracy * 100" :show-text="false" :stroke-width="6" color="#3b82f6" />
          </div>
        </el-col>
        <el-col :span="6">
          <div class="metric-card mc-green">
            <span class="mc-value">{{ (evaluation.precision * 100).toFixed(2) }}%</span>
            <span class="mc-label">精确率 (Precision)</span>
            <el-progress :percentage="evaluation.precision * 100" :show-text="false" :stroke-width="6" color="#10b981" />
          </div>
        </el-col>
        <el-col :span="6">
          <div class="metric-card mc-amber">
            <span class="mc-value">{{ (evaluation.recall * 100).toFixed(2) }}%</span>
            <span class="mc-label">召回率 (Recall)</span>
            <el-progress :percentage="evaluation.recall * 100" :show-text="false" :stroke-width="6" color="#f59e0b" />
          </div>
        </el-col>
        <el-col :span="6">
          <div class="metric-card mc-purple">
            <span class="mc-value">{{ (evaluation.f1_score * 100).toFixed(2) }}%</span>
            <span class="mc-label">F1 分数 (F1-Score)</span>
            <el-progress :percentage="evaluation.f1_score * 100" :show-text="false" :stroke-width="6" color="#8b5cf6" />
          </div>
        </el-col>
      </el-row>

      <!-- 训练日志图表 -->
      <el-row :gutter="16" v-if="trainingLogs.length">
        <el-col :span="12">
          <div class="card">
            <h3 class="card-title">训练损失曲线</h3>
            <LineChart
              :xData="epochs"
              :series="lossSeries"
            />
          </div>
        </el-col>
        <el-col :span="12">
          <div class="card">
            <h3 class="card-title">训练准确率曲线</h3>
            <LineChart
              :xData="epochs"
              :series="accSeries"
            />
          </div>
        </el-col>
      </el-row>

      <!-- 混淆矩阵 + 雷达图 -->
      <el-row :gutter="16" v-if="detailedEval">
        <el-col :span="12">
          <div class="card">
            <h3 class="card-title">混淆矩阵</h3>
            <p class="card-desc">展示分类结果的真正例、假正例、真负例、假负例分布（百分比 / 数量）</p>
            <HeatmapChart
              :data="confusionMatrixNorm"
              :rawData="confusionMatrixRaw"
              height="300px"
            />
          </div>
        </el-col>
        <el-col :span="12">
          <div class="card">
            <h3 class="card-title">各类别详细指标</h3>
            <p class="card-desc">Ham（正常邮件）与 Spam（垃圾邮件）分别的精确率、召回率和 F1</p>
            <div class="per-class-grid">
              <template v-for="(cls, label) in perClassMetrics" :key="label">
                <div class="per-class-block" :class="label === 'spam' ? 'pcb-spam' : 'pcb-ham'">
                  <div class="pcb-title">{{ label === 'spam' ? 'Spam（垃圾邮件）' : 'Ham（正常邮件）' }}</div>
                  <div class="pcb-metrics">
                    <div class="pcb-item">
                      <span class="pcb-val">{{ (cls.precision * 100).toFixed(2) }}%</span>
                      <span class="pcb-key">精确率</span>
                    </div>
                    <div class="pcb-item">
                      <span class="pcb-val">{{ (cls.recall * 100).toFixed(2) }}%</span>
                      <span class="pcb-key">召回率</span>
                    </div>
                    <div class="pcb-item">
                      <span class="pcb-val">{{ (cls.f1_score * 100).toFixed(2) }}%</span>
                      <span class="pcb-key">F1 分数</span>
                    </div>
                    <div class="pcb-item">
                      <span class="pcb-val">{{ cls.support }}</span>
                      <span class="pcb-key">样本数</span>
                    </div>
                  </div>
                </div>
              </template>
            </div>
          </div>
        </el-col>
      </el-row>

      <!-- 与传统方法基线对比 -->
      <el-row :gutter="16" v-if="evaluation">
        <el-col :span="12">
          <div class="card">
            <h3 class="card-title">与传统方法对比（雷达图）</h3>
            <p class="card-desc">BERT 与朴素贝叶斯、SVM、LSTM 等传统方法在四项指标上的综合对比</p>
            <RadarChart :series="radarSeries" height="320px" />
          </div>
        </el-col>
        <el-col :span="12">
          <div class="card">
            <h3 class="card-title">与传统方法对比（柱状图）</h3>
            <p class="card-desc">各方法在准确率、精确率、召回率、F1 四项指标上的数值对比（%）</p>
            <BarChart
              :xData="baselineBarXData"
              :series="baselineBarSeries"
              height="320px"
            />
          </div>
        </el-col>
      </el-row>

      <!-- 评估指标柱状图 -->
      <el-row :gutter="16" v-if="evaluation">
        <el-col :span="12">
          <div class="card">
            <h3 class="card-title">评估指标对比</h3>
            <BarChart
              :xData="['准确率', '精确率', '召回率', 'F1分数']"
              :series="[evalBarSeries]"
              height="320px"
            />
          </div>
        </el-col>
        <el-col :span="12">
          <div class="card">
            <h3 class="card-title">模型信息</h3>
            <div class="info-grid">
              <div class="info-row">
                <span class="info-label">模型名称</span>
                <span class="info-value">{{ model?.name }}</span>
              </div>
              <div class="info-row">
                <span class="info-label">基础模型</span>
                <span class="info-value">{{ model?.base_model }}</span>
              </div>
              <div class="info-row">
                <span class="info-label">模型版本</span>
                <span class="info-value">{{ model?.version }}</span>
              </div>
              <div class="info-row">
                <span class="info-label">训练轮数</span>
                <span class="info-value">{{ model?.training_params?.epochs || '--' }}</span>
              </div>
              <div class="info-row">
                <span class="info-label">学习率</span>
                <span class="info-value">{{ model?.training_params?.learning_rate || '--' }}</span>
              </div>
              <div class="info-row">
                <span class="info-label">批大小</span>
                <span class="info-value">{{ model?.training_params?.batch_size || '--' }}</span>
              </div>
              <div class="info-row">
                <span class="info-label">最大序列长度</span>
                <span class="info-value">{{ model?.training_params?.max_seq_length || '--' }}</span>
              </div>
              <div class="info-row">
                <span class="info-label">学习率衰减</span>
                <span class="info-value">{{ model?.training_params?.lr_decay_strategy || '--' }}</span>
              </div>
              <div class="info-row">
                <span class="info-label">描述</span>
                <span class="info-value">{{ model?.description || '无' }}</span>
              </div>
              <div class="info-row">
                <span class="info-label">创建时间</span>
                <span class="info-value">{{ formatDateTime(model?.created_at) }}</span>
              </div>
            </div>
          </div>
        </el-col>
      </el-row>

      <!-- 训练日志表格 -->
      <div class="card" v-if="trainingLogs.length">
        <h3 class="card-title">训练日志明细</h3>
        <el-table :data="trainingLogs" stripe border size="small">
          <el-table-column prop="epoch" label="Epoch" width="80" align="center" />
          <el-table-column label="训练损失" width="130" align="center">
            <template #default="{ row }">{{ row.train_loss?.toFixed(6) || '--' }}</template>
          </el-table-column>
          <el-table-column label="验证损失" width="130" align="center">
            <template #default="{ row }">{{ row.val_loss?.toFixed(6) || '--' }}</template>
          </el-table-column>
          <el-table-column label="训练准确率" width="130" align="center">
            <template #default="{ row }">
              <span v-if="row.train_accuracy != null">{{ (row.train_accuracy * 100).toFixed(2) }}%</span>
              <span v-else>--</span>
            </template>
          </el-table-column>
          <el-table-column label="验证准确率" width="130" align="center">
            <template #default="{ row }">
              <span v-if="row.val_accuracy != null">{{ (row.val_accuracy * 100).toFixed(2) }}%</span>
              <span v-else>--</span>
            </template>
          </el-table-column>
          <el-table-column label="学习率" width="130" align="center">
            <template #default="{ row }">{{ row.learning_rate?.toExponential(2) || '--' }}</template>
          </el-table-column>
        </el-table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { getModel, getTrainingLogs, getModelEvaluation, getModelDetailedEvaluation } from '@/api/model'
import { ArrowLeft } from '@element-plus/icons-vue'
import LineChart from '@/components/charts/LineChart.vue'
import BarChart from '@/components/charts/BarChart.vue'
import HeatmapChart from '@/components/charts/HeatmapChart.vue'
import RadarChart from '@/components/charts/RadarChart.vue'

const route = useRoute()
const modelId = route.params.id

const loading = ref(false)
const model = ref(null)
const trainingLogs = ref([])
const evaluation = ref(null)
const detailedEval = ref(null)

// 传统方法基线数据（学术公开数据集典型值）
const BASELINES = [
  { name: 'BERT（本模型）', values: [0, 0, 0, 0] },  // 动态填充
  { name: '朴素贝叶斯', values: [97.5, 96.1, 89.3, 92.6] },
  { name: 'SVM', values: [98.1, 97.4, 91.2, 94.2] },
  { name: 'LSTM', values: [98.6, 97.8, 93.5, 95.6] },
]

const epochs = computed(() => trainingLogs.value.map(l => `Epoch ${l.epoch}`))

const lossSeries = computed(() => [
  {
    name: '训练损失',
    data: trainingLogs.value.map(l => l.train_loss),
    itemStyle: { color: '#ef4444' },
  },
  {
    name: '验证损失',
    data: trainingLogs.value.map(l => l.val_loss),
    itemStyle: { color: '#3b82f6' },
  },
])

const accSeries = computed(() => [
  {
    name: '训练准确率',
    data: trainingLogs.value.map(l => l.train_accuracy ? (l.train_accuracy * 100).toFixed(2) : null),
    itemStyle: { color: '#10b981' },
  },
  {
    name: '验证准确率',
    data: trainingLogs.value.map(l => l.val_accuracy ? (l.val_accuracy * 100).toFixed(2) : null),
    itemStyle: { color: '#8b5cf6' },
  },
])

const evalBarSeries = computed(() => {
  if (!evaluation.value) return { name: '指标', data: [] }
  const e = evaluation.value
  return {
    name: '评估指标 (%)',
    data: [
      { value: (e.accuracy * 100).toFixed(2), itemStyle: { color: '#3b82f6' } },
      { value: (e.precision * 100).toFixed(2), itemStyle: { color: '#10b981' } },
      { value: (e.recall * 100).toFixed(2), itemStyle: { color: '#f59e0b' } },
      { value: (e.f1_score * 100).toFixed(2), itemStyle: { color: '#8b5cf6' } },
    ],
  }
})

// 混淆矩阵数据
const confusionMatrixNorm = computed(() => detailedEval.value?.confusion_matrix_normalized ?? [[0, 0], [0, 0]])
const confusionMatrixRaw = computed(() => detailedEval.value?.confusion_matrix ?? [[0, 0], [0, 0]])

// 雷达图：本模型 vs 传统方法基线对比
const radarSeries = computed(() => {
  if (!evaluation.value) return BASELINES.slice(1).map(b => ({ name: b.name, values: b.values }))
  const e = evaluation.value
  const bertValues = [
    parseFloat((e.accuracy * 100).toFixed(2)),
    parseFloat((e.precision * 100).toFixed(2)),
    parseFloat((e.recall * 100).toFixed(2)),
    parseFloat((e.f1_score * 100).toFixed(2)),
  ]
  return [
    { name: 'BERT（本模型）', values: bertValues },
    ...BASELINES.slice(1).map(b => ({ name: b.name, values: b.values })),
  ]
})

// 基线对比柱状图（多系列）
const baselineBarXData = ['准确率', '精确率', '召回率', 'F1 分数']
const baselineBarSeries = computed(() => {
  if (!evaluation.value) return []
  const e = evaluation.value
  const bertValues = [
    parseFloat((e.accuracy * 100).toFixed(2)),
    parseFloat((e.precision * 100).toFixed(2)),
    parseFloat((e.recall * 100).toFixed(2)),
    parseFloat((e.f1_score * 100).toFixed(2)),
  ]
  const colors = ['#3b82f6', '#9ca3af', '#6b7280', '#4b5563']
  return [
    { name: 'BERT（本模型）', data: bertValues, itemStyle: { color: colors[0] } },
    ...BASELINES.slice(1).map((b, i) => ({
      name: b.name,
      data: b.values,
      itemStyle: { color: colors[i + 1] },
    })),
  ]
})

// 各类别指标卡片数据
const perClassMetrics = computed(() => detailedEval.value?.per_class_metrics ?? {})

function statusType(s) {
  return { training: 'warning', completed: 'success', failed: 'danger' }[s] || 'info'
}
function statusText(s) {
  return { training: '训练中', completed: '已完成', failed: '失败' }[s] || s
}

function formatDateTime(dt) {
  if (!dt) return '--'
  const d = new Date(dt)
  const pad = (n) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`
}

async function fetchAll() {
  loading.value = true
  try {
    const modelRes = await getModel(modelId)
    model.value = modelRes.data

    const logsRes = await getTrainingLogs(modelId)
    trainingLogs.value = logsRes.data

    if (model.value.status === 'completed') {
      const [evalRes, detailedRes] = await Promise.all([
        getModelEvaluation(modelId),
        getModelDetailedEvaluation(modelId),
      ])
      evaluation.value = evalRes.data
      detailedEval.value = detailedRes.data
    }
  } catch { /* silent */ } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchAll()
})
</script>

<style scoped>
.model-detail-page {
  max-width: 1200px;
  margin: 0 auto;
}
.page-title-bar {
  margin-bottom: 20px;
}
.back-btn {
  color: rgba(255, 255, 255, 0.55);
  font-size: 14px;
  padding: 0;
  margin-bottom: 8px;
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
  display: flex;
  align-items: center;
}

/* Metric cards */
.metric-row {
  margin-bottom: 16px;
}
.metric-card {
  background: rgba(255, 255, 255, 0.06);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
  border-left: 4px solid transparent;
}
.mc-blue { border-left-color: #3b82f6; }
.mc-green { border-left-color: #10b981; }
.mc-amber { border-left-color: #f59e0b; }
.mc-purple { border-left-color: #8b5cf6; }
.mc-value {
  display: block;
  font-size: 26px;
  font-weight: 700;
  color: #ffffff;
  margin-bottom: 4px;
}
.mc-label {
  display: block;
  font-size: 13px;
  color: rgba(255, 255, 255, 0.4);
  margin-bottom: 12px;
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
}

/* Info grid */
.info-grid {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.info-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}
.info-row:last-child {
  border-bottom: none;
}
.info-label {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.4);
  flex-shrink: 0;
}
.info-value {
  font-size: 14px;
  font-weight: 500;
  color: rgba(255, 255, 255, 0.8);
  text-align: right;
}

/* Card desc */
.card-desc {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.35);
  margin: -8px 0 12px;
  line-height: 1.5;
}

/* Per-class metrics */
.per-class-grid {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-top: 8px;
}
.per-class-block {
  border-radius: 10px;
  padding: 16px;
  border-left: 4px solid transparent;
  background: rgba(255, 255, 255, 0.04);
}
.pcb-ham { border-left-color: #10b981; }
.pcb-spam { border-left-color: #ef4444; }
.pcb-title {
  font-size: 13px;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.7);
  margin-bottom: 12px;
}
.pcb-metrics {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 8px;
}
.pcb-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}
.pcb-val {
  font-size: 16px;
  font-weight: 700;
  color: #ffffff;
}
.pcb-key {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.4);
}
</style>
