<template>
  <div class="analysis-page">
    <div class="page-title-bar">
      <div>
        <h2>{{ userStore.isAdmin ? '数据分析' : '结果分析' }}</h2>
        <p class="page-desc">{{ userStore.isAdmin ? '汇总展示所有预测结果，包含分类标签、置信度和预测时间，支持导出 CSV' : '可视化查看预测结果的分类分布、置信度与趋势变化' }}</p>
      </div>
      <el-button type="primary" class="export-btn" @click="handleExportCSV" :disabled="!historyList.length">
        <el-icon><Download /></el-icon>
        导出 CSV
      </el-button>
    </div>

    <!-- 概览统计卡片 -->
    <el-row :gutter="16" class="stat-row">
      <el-col :span="6">
        <div class="stat-card">
          <div class="stat-icon bg-blue"><el-icon :size="24"><DataAnalysis /></el-icon></div>
          <div class="stat-body">
            <span class="stat-value">{{ overview.total_predictions }}</span>
            <span class="stat-label">预测总数</span>
          </div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="stat-card">
          <div class="stat-icon bg-red"><el-icon :size="24"><WarningFilled /></el-icon></div>
          <div class="stat-body">
            <span class="stat-value text-red">{{ overview.spam_predictions }}</span>
            <span class="stat-label">垃圾邮件</span>
          </div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="stat-card">
          <div class="stat-icon bg-green"><el-icon :size="24"><CircleCheckFilled /></el-icon></div>
          <div class="stat-body">
            <span class="stat-value text-green">{{ overview.ham_predictions }}</span>
            <span class="stat-label">正常邮件</span>
          </div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="stat-card">
          <div class="stat-icon bg-purple"><el-icon :size="24"><Aim /></el-icon></div>
          <div class="stat-body">
            <span class="stat-value text-purple">{{ (overview.avg_confidence * 100).toFixed(1) }}%</span>
            <span class="stat-label">平均置信度</span>
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- 图表区域 -->
    <el-row :gutter="16">
      <el-col :span="12">
        <div class="card">
          <h3 class="card-title">分类分布</h3>
          <PieChart :data="pieData" />
        </div>
      </el-col>
      <el-col :span="12">
        <div class="card">
          <h3 class="card-title">置信度分布</h3>
          <BarChart
            :xData="confDist.map(d => d.range)"
            :series="confSeries"
            height="300px"
          />
        </div>
      </el-col>
    </el-row>

    <!-- 预测趋势 -->
    <div class="card">
      <div class="card-header">
        <h3 class="card-title">预测趋势</h3>
        <el-radio-group v-model="trendDays" size="small" @change="fetchTrend">
          <el-radio-button :value="7">7天</el-radio-button>
          <el-radio-button :value="14">14天</el-radio-button>
          <el-radio-button :value="30">30天</el-radio-button>
        </el-radio-group>
      </div>
      <LineChart
        :xData="trendDates"
        :series="trendSeries"
      />
    </div>

    <!-- 预测结果列表 -->
    <div class="card">
      <div class="card-header">
        <h3 class="card-title">预测结果明细</h3>
        <span class="record-count">共 {{ totalCount }} 条记录</span>
      </div>
      <el-table :data="historyList" stripe border size="default" v-loading="tableLoading" max-height="500">
        <el-table-column type="index" label="#" width="60" align="center" />
        <el-table-column prop="input_text" label="邮件内容" min-width="300" show-overflow-tooltip />
        <el-table-column label="分类标签" width="120" align="center">
          <template #default="{ row }">
            <el-tag :type="row.prediction_label === 'spam' ? 'danger' : 'success'" effect="dark" round>
              {{ row.prediction_label === 'spam' ? '垃圾邮件' : '正常邮件' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="置信度" width="150" align="center">
          <template #default="{ row }">
            <div class="conf-cell">
              <el-progress
                :percentage="Number((row.confidence * 100).toFixed(1))"
                :color="row.prediction_label === 'spam' ? '#ef4444' : '#10b981'"
                :stroke-width="8"
                :show-text="false"
                style="flex: 1"
              />
              <span class="conf-text">{{ (row.confidence * 100).toFixed(1) }}%</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="预测时间" width="180" align="center">
          <template #default="{ row }">
            {{ formatDateTime(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="处理耗时" width="100" align="center">
          <template #default="{ row }">
            {{ row.processing_time ? row.processing_time.toFixed(3) + 's' : '--' }}
          </template>
        </el-table-column>
      </el-table>
      <div class="pagination-wrap">
        <el-pagination
          v-model:current-page="page"
          :page-size="pageSize"
          :total="totalCount"
          layout="total, prev, pager, next, jumper"
          @current-change="fetchHistory"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { getPredictionHistory, getPredictionCount } from '@/api/prediction'
import { getOverview, getPredictionTrend, getConfidenceDistribution } from '@/api/analysis'
import { ElMessage } from 'element-plus'
import Papa from 'papaparse'
import { useUserStore } from '@/store/modules/user'
import {
  Download, DataAnalysis, WarningFilled, CircleCheckFilled, Aim,
} from '@element-plus/icons-vue'

const userStore = useUserStore()
import PieChart from '@/components/charts/PieChart.vue'
import BarChart from '@/components/charts/BarChart.vue'
import LineChart from '@/components/charts/LineChart.vue'

const overview = ref({
  total_predictions: 0, spam_predictions: 0, ham_predictions: 0, avg_confidence: 0,
})
const historyList = ref([])
const tableLoading = ref(false)
const totalCount = ref(0)
const page = ref(1)
const pageSize = 20

const trendDays = ref(30)
const trendData = ref([])
const confDist = ref([])

const pieData = computed(() => [
  { name: '垃圾邮件', value: overview.value.spam_predictions, itemStyle: { color: '#ef4444' } },
  { name: '正常邮件', value: overview.value.ham_predictions, itemStyle: { color: '#10b981' } },
])

const confSeries = computed(() => [
  { name: '垃圾邮件', data: confDist.value.map(d => d.spam), itemStyle: { color: '#ef4444' } },
  { name: '正常邮件', data: confDist.value.map(d => d.ham), itemStyle: { color: '#10b981' } },
])

const trendDates = computed(() => trendData.value.map(d => d.date))
const trendSeries = computed(() => [
  { name: '垃圾邮件', data: trendData.value.map(d => d.spam), itemStyle: { color: '#ef4444' } },
  { name: '正常邮件', data: trendData.value.map(d => d.ham), itemStyle: { color: '#10b981' } },
  { name: '总计', data: trendData.value.map(d => d.total), itemStyle: { color: '#6366f1' } },
])

function formatDateTime(dt) {
  if (!dt) return '--'
  const d = new Date(dt)
  const pad = (n) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`
}

async function fetchOverview() {
  try {
    const res = await getOverview()
    overview.value = res.data
  } catch { /* silent */ }
}

async function fetchHistory() {
  tableLoading.value = true
  try {
    const [histRes, countRes] = await Promise.all([
      getPredictionHistory({ page: page.value, page_size: pageSize }),
      getPredictionCount({}),
    ])
    historyList.value = histRes.data
    totalCount.value = countRes.data.count
  } catch { /* silent */ } finally {
    tableLoading.value = false
  }
}

async function fetchTrend() {
  try {
    const res = await getPredictionTrend(trendDays.value)
    trendData.value = res.data
  } catch { /* silent */ }
}

async function fetchConfDist() {
  try {
    const res = await getConfidenceDistribution()
    confDist.value = res.data
  } catch { /* silent */ }
}

function handleExportCSV() {
  if (!historyList.value.length) return

  const exportData = historyList.value.map((row, idx) => ({
    '序号': idx + 1,
    '邮件内容': row.input_text,
    '分类标签': row.prediction_label === 'spam' ? '垃圾邮件' : '正常邮件',
    '分类代码': row.prediction_label,
    '置信度': (row.confidence * 100).toFixed(2) + '%',
    '处理耗时(s)': row.processing_time?.toFixed(4) || '',
    '预测时间': formatDateTime(row.created_at),
  }))

  const csv = Papa.unparse(exportData)
  const bom = '\uFEFF'
  const blob = new Blob([bom + csv], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `prediction_results_${new Date().toISOString().slice(0, 10)}.csv`
  a.click()
  URL.revokeObjectURL(url)
  ElMessage.success('CSV 导出成功')
}

onMounted(() => {
  fetchOverview()
  fetchHistory()
  fetchTrend()
  fetchConfDist()
})
</script>

<style scoped>
.analysis-page {
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
.export-btn {
  border-radius: 10px;
  font-weight: 600;
  background: linear-gradient(135deg, #4f46e5, #7c3aed);
  border: none;
}
.export-btn:hover:not(:disabled) {
  background: linear-gradient(135deg, #4338ca, #6d28d9);
}

/* Stat cards */
.stat-row {
  margin-bottom: 16px;
}
.stat-card {
  background: rgba(255, 255, 255, 0.06);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
  display: flex;
  align-items: center;
  gap: 16px;
}
.stat-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  flex-shrink: 0;
}
.bg-blue { background: linear-gradient(135deg, #3b82f6, #6366f1); }
.bg-red { background: linear-gradient(135deg, #ef4444, #f97316); }
.bg-green { background: linear-gradient(135deg, #10b981, #14b8a6); }
.bg-purple { background: linear-gradient(135deg, #8b5cf6, #a855f7); }
.stat-body {
  display: flex;
  flex-direction: column;
}
.stat-value {
  font-size: 24px;
  font-weight: 700;
  color: #ffffff;
  line-height: 1.2;
}
.text-red { color: #ef4444; }
.text-green { color: #10b981; }
.text-purple { color: #8b5cf6; }
.stat-label {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.4);
  margin-top: 2px;
}

/* Cards */
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
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}
.card-header .card-title {
  margin-bottom: 0;
}
.record-count {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.4);
}

/* Confidence cell */
.conf-cell {
  display: flex;
  align-items: center;
  gap: 8px;
}
.conf-text {
  font-size: 13px;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.8);
  flex-shrink: 0;
  width: 48px;
  text-align: right;
}

/* Pagination */
.pagination-wrap {
  display: flex;
  justify-content: center;
  margin-top: 16px;
}
</style>
