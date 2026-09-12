<template>
  <div class="model-eval-page">
    <div class="page-title-bar">
      <div>
        <h2>{{ userStore.isAdmin ? '模型评估' : '模型概览' }}</h2>
        <p class="page-desc">{{ userStore.isAdmin ? '查看各模型的训练结果与评估指标，通过图表对比模型性能' : '查看当前可用模型的性能表现与运行状态' }}</p>
      </div>
      <el-radio-group v-if="userStore.isAdmin" v-model="chartType" size="small">
        <el-radio-button value="bar">柱状图</el-radio-button>
        <el-radio-button value="line">折线图</el-radio-button>
      </el-radio-group>
    </div>

    <!-- 指标对比图表 (管理员可见完整图表，用户仅看雷达图 + 激活模型信息) -->
    <div v-if="userStore.isAdmin" class="card" v-loading="loading">
      <h3 class="card-title">模型指标对比</h3>
      <div v-if="models.length === 0 && !loading" class="empty-chart">
        <el-icon :size="48" color="#e5e7eb"><DataLine /></el-icon>
        <p>暂无已完成训练的模型</p>
      </div>
      <template v-else>
        <div v-if="chartType === 'bar'">
          <BarChart
            :xData="modelNames"
            :series="barSeries"
            height="380px"
          />
        </div>
        <div v-else>
          <LineChart
            :xData="modelNames"
            :series="lineSeries"
          />
        </div>
      </template>
    </div>

    <!-- 雷达图 + 活跃模型信息 -->
    <el-row :gutter="16" v-if="models.length">
      <el-col :span="12">
        <div class="card">
          <h3 class="card-title">当前激活模型指标雷达图</h3>
          <div ref="radarChartRef" style="width: 100%; height: 350px"></div>
        </div>
      </el-col>
      <el-col :span="12">
        <div class="card">
          <h3 class="card-title">指标详情</h3>
          <div v-if="activeModel" class="active-model-info">
            <div class="ami-header">
              <el-tag type="success" effect="dark" round>当前激活</el-tag>
              <span class="ami-name">{{ activeModel.name }}</span>
            </div>
            <div class="metric-grid">
              <div class="metric-item">
                <div class="metric-ring" style="--ring-color: #3b82f6">
                  <svg viewBox="0 0 36 36">
                    <path class="ring-bg" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" />
                    <path class="ring-fg" :stroke-dasharray="`${(activeModel.accuracy || 0) * 100}, 100`" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" />
                  </svg>
                  <span class="ring-val">{{ ((activeModel.accuracy || 0) * 100).toFixed(1) }}%</span>
                </div>
                <span class="metric-name">准确率</span>
              </div>
              <div class="metric-item">
                <div class="metric-ring" style="--ring-color: #10b981">
                  <svg viewBox="0 0 36 36">
                    <path class="ring-bg" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" />
                    <path class="ring-fg" :stroke-dasharray="`${(activeModel.precision || 0) * 100}, 100`" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" />
                  </svg>
                  <span class="ring-val">{{ ((activeModel.precision || 0) * 100).toFixed(1) }}%</span>
                </div>
                <span class="metric-name">精确率</span>
              </div>
              <div class="metric-item">
                <div class="metric-ring" style="--ring-color: #f59e0b">
                  <svg viewBox="0 0 36 36">
                    <path class="ring-bg" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" />
                    <path class="ring-fg" :stroke-dasharray="`${(activeModel.recall || 0) * 100}, 100`" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" />
                  </svg>
                  <span class="ring-val">{{ ((activeModel.recall || 0) * 100).toFixed(1) }}%</span>
                </div>
                <span class="metric-name">召回率</span>
              </div>
              <div class="metric-item">
                <div class="metric-ring" style="--ring-color: #8b5cf6">
                  <svg viewBox="0 0 36 36">
                    <path class="ring-bg" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" />
                    <path class="ring-fg" :stroke-dasharray="`${(activeModel.f1_score || 0) * 100}, 100`" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" />
                  </svg>
                  <span class="ring-val">{{ ((activeModel.f1_score || 0) * 100).toFixed(1) }}%</span>
                </div>
                <span class="metric-name">F1 分数</span>
              </div>
            </div>
          </div>
          <div v-else class="no-active">
            <p>暂无激活模型，请在模型列表中激活一个模型</p>
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- 模型列表 -->
    <div class="card">
      <h3 class="card-title">{{ userStore.isAdmin ? '模型列表' : '可用模型' }}</h3>

      <!-- 管理员完整表格 -->
      <el-table v-if="userStore.isAdmin" :data="models" stripe border size="default" v-loading="loading">
        <el-table-column prop="name" label="模型名称" min-width="160">
          <template #default="{ row }">
            <router-link :to="`/model/${row.id}`" class="model-link">
              {{ row.name }}
              <el-tag v-if="row.is_active" type="success" size="small" style="margin-left: 6px">激活</el-tag>
            </router-link>
          </template>
        </el-table-column>
        <el-table-column prop="base_model" label="基础模型" width="160" />
        <el-table-column label="准确率" width="100" align="center">
          <template #default="{ row }">
            <span :class="metricClass(row.accuracy)">{{ formatPct(row.accuracy) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="精确率" width="100" align="center">
          <template #default="{ row }">
            <span :class="metricClass(row.precision)">{{ formatPct(row.precision) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="召回率" width="100" align="center">
          <template #default="{ row }">
            <span :class="metricClass(row.recall)">{{ formatPct(row.recall) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="F1 分数" width="100" align="center">
          <template #default="{ row }">
            <span :class="metricClass(row.f1_score)">{{ formatPct(row.f1_score) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="statusType(row.status)" size="small">{{ statusText(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="100" align="center">
          <template #default="{ row }">
            <el-button type="primary" link size="small" @click="$router.push(`/model/${row.id}`)">
              详情
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 普通用户精简表格 -->
      <el-table v-else :data="models" stripe border size="default" v-loading="loading">
        <el-table-column prop="name" label="模型名称" min-width="200">
          <template #default="{ row }">
            <router-link :to="`/model/${row.id}`" class="model-link">
              {{ row.name }}
              <el-tag v-if="row.is_active" type="success" size="small" style="margin-left: 6px">当前使用</el-tag>
            </router-link>
          </template>
        </el-table-column>
        <el-table-column label="准确率" width="160" align="center">
          <template #default="{ row }">
            <div v-if="row.accuracy != null" class="user-metric-cell">
              <el-progress
                :percentage="Number((row.accuracy * 100).toFixed(1))"
                :color="row.accuracy >= 0.9 ? '#10b981' : row.accuracy >= 0.7 ? '#f59e0b' : '#ef4444'"
                :stroke-width="8"
                :show-text="false"
                style="flex: 1"
              />
              <span class="user-metric-val">{{ formatPct(row.accuracy) }}</span>
            </div>
            <span v-else class="metric-na">--</span>
          </template>
        </el-table-column>
        <el-table-column label="F1 分数" width="160" align="center">
          <template #default="{ row }">
            <div v-if="row.f1_score != null" class="user-metric-cell">
              <el-progress
                :percentage="Number((row.f1_score * 100).toFixed(1))"
                :color="row.f1_score >= 0.9 ? '#10b981' : row.f1_score >= 0.7 ? '#f59e0b' : '#ef4444'"
                :stroke-width="8"
                :show-text="false"
                style="flex: 1"
              />
              <span class="user-metric-val">{{ formatPct(row.f1_score) }}</span>
            </div>
            <span v-else class="metric-na">--</span>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="statusType(row.status)" size="small">{{ statusText(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="100" align="center">
          <template #default="{ row }">
            <el-button type="primary" link size="small" @click="$router.push(`/model/${row.id}`)">
              查看
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch, nextTick } from 'vue'
import { useUserStore } from '@/store/modules/user'
import { getModels } from '@/api/model'
import { getModelComparison } from '@/api/analysis'
import { DataLine } from '@element-plus/icons-vue'
import BarChart from '@/components/charts/BarChart.vue'
import LineChart from '@/components/charts/LineChart.vue'
import * as echarts from 'echarts/core'
import { RadarChart } from 'echarts/charts'
import { TitleComponent, TooltipComponent, LegendComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'

echarts.use([RadarChart, TitleComponent, TooltipComponent, LegendComponent, CanvasRenderer])

const userStore = useUserStore()
const loading = ref(false)
const models = ref([])
const chartType = ref('bar')
const radarChartRef = ref(null)
let radarInstance = null

const activeModel = computed(() => models.value.find(m => m.is_active) || null)

const modelNames = computed(() => models.value.filter(m => m.status === 'completed').map(m => m.name))

const completedModels = computed(() => models.value.filter(m => m.status === 'completed'))

const metricColors = {
  accuracy: '#3b82f6',
  precision: '#10b981',
  recall: '#f59e0b',
  f1_score: '#8b5cf6',
}

const barSeries = computed(() => [
  { name: '准确率', data: completedModels.value.map(m => ((m.accuracy || 0) * 100).toFixed(2)), itemStyle: { color: metricColors.accuracy } },
  { name: '精确率', data: completedModels.value.map(m => ((m.precision || 0) * 100).toFixed(2)), itemStyle: { color: metricColors.precision } },
  { name: '召回率', data: completedModels.value.map(m => ((m.recall || 0) * 100).toFixed(2)), itemStyle: { color: metricColors.recall } },
  { name: 'F1 分数', data: completedModels.value.map(m => ((m.f1_score || 0) * 100).toFixed(2)), itemStyle: { color: metricColors.f1_score } },
])

const lineSeries = computed(() => [
  { name: '准确率', data: completedModels.value.map(m => ((m.accuracy || 0) * 100).toFixed(2)), itemStyle: { color: metricColors.accuracy } },
  { name: '精确率', data: completedModels.value.map(m => ((m.precision || 0) * 100).toFixed(2)), itemStyle: { color: metricColors.precision } },
  { name: '召回率', data: completedModels.value.map(m => ((m.recall || 0) * 100).toFixed(2)), itemStyle: { color: metricColors.recall } },
  { name: 'F1 分数', data: completedModels.value.map(m => ((m.f1_score || 0) * 100).toFixed(2)), itemStyle: { color: metricColors.f1_score } },
])

function formatPct(val) {
  if (val == null) return '--'
  return (val * 100).toFixed(2) + '%'
}

function metricClass(val) {
  if (val == null) return 'metric-na'
  if (val >= 0.9) return 'metric-high'
  if (val >= 0.7) return 'metric-mid'
  return 'metric-low'
}

function statusType(s) {
  return { training: 'warning', completed: 'success', failed: 'danger' }[s] || 'info'
}
function statusText(s) {
  return { training: '训练中', completed: '已完成', failed: '失败' }[s] || s
}

function initRadarChart() {
  if (!radarChartRef.value || !activeModel.value) return

  if (radarInstance) radarInstance.dispose()
  radarInstance = echarts.init(radarChartRef.value)

  const m = activeModel.value
  radarInstance.setOption({
    tooltip: {},
    radar: {
      indicator: [
        { name: '准确率', max: 100 },
        { name: '精确率', max: 100 },
        { name: '召回率', max: 100 },
        { name: 'F1 分数', max: 100 },
      ],
      shape: 'circle',
      splitArea: { areaStyle: { color: ['rgba(99, 102, 241, 0.02)', 'rgba(99, 102, 241, 0.06)'] } },
    },
    series: [{
      type: 'radar',
      data: [{
        value: [
          ((m.accuracy || 0) * 100).toFixed(1),
          ((m.precision || 0) * 100).toFixed(1),
          ((m.recall || 0) * 100).toFixed(1),
          ((m.f1_score || 0) * 100).toFixed(1),
        ],
        name: m.name,
        areaStyle: { color: 'rgba(99, 102, 241, 0.15)' },
        lineStyle: { color: '#6366f1', width: 2 },
        itemStyle: { color: '#6366f1' },
      }],
    }],
  })
}

async function fetchModels() {
  loading.value = true
  try {
    const res = await getModels()
    models.value = res.data
    await nextTick()
    initRadarChart()
  } catch { /* silent */ } finally {
    loading.value = false
  }
}

watch(() => activeModel.value, () => {
  nextTick(() => initRadarChart())
})

onMounted(() => {
  fetchModels()
})
</script>

<style scoped>
.model-eval-page {
  max-width: 1200px;
  margin: 0 auto;
}
.page-title-bar {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
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
}

.empty-chart {
  text-align: center;
  padding: 60px 0;
}
.empty-chart p {
  color: rgba(255, 255, 255, 0.4);
  margin-top: 12px;
}

/* Active model info */
.active-model-info {
  padding: 8px 0;
}
.ami-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 24px;
}
.ami-name {
  font-size: 18px;
  font-weight: 700;
  color: #ffffff;
}
.metric-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
}
.metric-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}
.metric-ring {
  position: relative;
  width: 90px;
  height: 90px;
}
.metric-ring svg {
  width: 100%;
  height: 100%;
  transform: rotate(-90deg);
}
.ring-bg {
  fill: none;
  stroke: rgba(255, 255, 255, 0.1);
  stroke-width: 3;
}
.ring-fg {
  fill: none;
  stroke: var(--ring-color);
  stroke-width: 3;
  stroke-linecap: round;
  transition: stroke-dasharray 0.6s ease;
}
.ring-val {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  font-size: 14px;
  font-weight: 700;
  color: #ffffff;
}
.metric-name {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.55);
}
.no-active {
  text-align: center;
  padding: 40px 0;
  color: rgba(255, 255, 255, 0.4);
}

/* Model link */
.model-link {
  color: #818cf8;
  text-decoration: none;
  font-weight: 500;
  display: inline-flex;
  align-items: center;
}
.model-link:hover {
  color: #a5b4fc;
  text-decoration: underline;
}

/* Metric colors */
.metric-high { color: #10b981; font-weight: 600; }
.metric-mid { color: #f59e0b; font-weight: 600; }
.metric-low { color: #ef4444; font-weight: 600; }
.metric-na { color: rgba(255, 255, 255, 0.4); }

/* User simplified metric cell */
.user-metric-cell {
  display: flex;
  align-items: center;
  gap: 8px;
}
.user-metric-val {
  font-size: 13px;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.8);
  flex-shrink: 0;
  width: 52px;
  text-align: right;
}
</style>
