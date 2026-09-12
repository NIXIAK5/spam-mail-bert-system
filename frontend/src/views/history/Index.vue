<template>
  <div class="history-page">
    <div class="page-title-bar">
      <div>
        <h2>{{ userStore.isAdmin ? '预测历史记录' : '我的记录' }}</h2>
        <p class="page-desc">{{ userStore.isAdmin ? '查看所有预测任务的完整历史，支持按时间范围和结果类型筛选' : '查看我的邮件检测记录，筛选和导出历史结果' }}</p>
      </div>
    </div>

    <!-- 筛选区域 -->
    <div class="card filter-card">
      <el-form :inline="true" class="filter-form">
        <el-form-item label="结果类型">
          <el-select v-model="filterLabel" placeholder="全部" clearable style="width: 140px">
            <el-option label="全部" value="" />
            <el-option label="垃圾邮件" value="spam" />
            <el-option label="正常邮件" value="ham" />
          </el-select>
        </el-form-item>
        <el-form-item label="时间范围">
          <el-date-picker
            v-model="dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            format="YYYY-MM-DD"
            value-format="YYYY-MM-DD"
            :shortcuts="dateShortcuts"
            style="width: 300px"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">
            <el-icon><Search /></el-icon>
            搜索
          </el-button>
          <el-button @click="handleReset">
            <el-icon><RefreshRight /></el-icon>
            重置
          </el-button>
          <el-button @click="handleExportCSV" :disabled="!historyList.length">
            <el-icon><Download /></el-icon>
            导出
          </el-button>
        </el-form-item>
      </el-form>
    </div>

    <!-- 统计概览 -->
    <el-row :gutter="12" class="mini-stats">
      <el-col :span="8">
        <div class="mini-stat-card">
          <span class="ms-value">{{ totalCount }}</span>
          <span class="ms-label">总记录数</span>
        </div>
      </el-col>
      <el-col :span="8">
        <div class="mini-stat-card ms-spam">
          <span class="ms-value">{{ spamCount }}</span>
          <span class="ms-label">垃圾邮件</span>
        </div>
      </el-col>
      <el-col :span="8">
        <div class="mini-stat-card ms-ham">
          <span class="ms-value">{{ hamCount }}</span>
          <span class="ms-label">正常邮件</span>
        </div>
      </el-col>
    </el-row>

    <!-- 历史列表 -->
    <div class="card">
      <el-table
        :data="historyList"
        stripe
        border
        size="default"
        v-loading="tableLoading"
        @row-click="handleRowClick"
        highlight-current-row
        class="history-table"
      >
        <el-table-column type="index" label="#" width="60" align="center" :index="indexMethod" />
        <el-table-column prop="input_text" label="邮件内容" min-width="280" show-overflow-tooltip>
          <template #default="{ row }">
            <span class="text-preview">{{ row.input_text }}</span>
          </template>
        </el-table-column>
        <el-table-column label="分类结果" width="120" align="center">
          <template #default="{ row }">
            <el-tag
              :type="row.prediction_label === 'spam' ? 'danger' : 'success'"
              effect="dark"
              round
              size="default"
            >
              <el-icon style="margin-right: 2px">
                <WarningFilled v-if="row.prediction_label === 'spam'" />
                <CircleCheckFilled v-else />
              </el-icon>
              {{ row.prediction_label === 'spam' ? '垃圾' : '正常' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="置信度" width="150" align="center" sortable :sort-method="sortByConfidence">
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
        <el-table-column label="处理耗时" width="110" align="center">
          <template #default="{ row }">
            {{ row.processing_time ? row.processing_time.toFixed(3) + 's' : '--' }}
          </template>
        </el-table-column>
        <el-table-column label="预测时间" width="180" align="center" sortable :sort-method="sortByDate">
          <template #default="{ row }">
            {{ formatDateTime(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="80" align="center" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link size="small" @click.stop="showDetail(row)">
              详情
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-wrap">
        <el-pagination
          v-model:current-page="page"
          v-model:page-size="pageSize"
          :page-sizes="[10, 20, 50, 100]"
          :total="totalCount"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handlePageChange"
        />
      </div>
    </div>

    <!-- 详情弹窗 -->
    <el-dialog v-model="detailVisible" title="预测详情" width="620px" :close-on-click-modal="true">
      <div v-if="currentDetail" class="detail-dialog">
        <div class="dd-result" :class="currentDetail.prediction_label === 'spam' ? 'dd-spam' : 'dd-ham'">
          <div class="dd-icon">
            <el-icon :size="36">
              <WarningFilled v-if="currentDetail.prediction_label === 'spam'" />
              <CircleCheckFilled v-else />
            </el-icon>
          </div>
          <div class="dd-label">
            {{ currentDetail.prediction_label === 'spam' ? '垃圾邮件' : '正常邮件' }}
          </div>
          <div class="dd-confidence">
            置信度：{{ (currentDetail.confidence * 100).toFixed(2) }}%
          </div>
        </div>

        <div class="dd-info-grid">
          <div class="dd-info-item">
            <span class="dd-info-label">处理耗时</span>
            <span class="dd-info-value">{{ currentDetail.processing_time ? currentDetail.processing_time.toFixed(4) + 's' : '--' }}</span>
          </div>
          <div class="dd-info-item">
            <span class="dd-info-label">预测时间</span>
            <span class="dd-info-value">{{ formatDateTime(currentDetail.created_at) }}</span>
          </div>
          <div class="dd-info-item">
            <span class="dd-info-label">记录 ID</span>
            <span class="dd-info-value">#{{ currentDetail.id }}</span>
          </div>
          <div class="dd-info-item">
            <span class="dd-info-label">文本长度</span>
            <span class="dd-info-value">{{ currentDetail.input_text.length }} 个字符</span>
          </div>
        </div>

        <div class="dd-text-section">
          <h4>邮件内容</h4>
          <div class="dd-text-body">{{ currentDetail.input_text }}</div>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getPredictionHistory, getPredictionCount } from '@/api/prediction'
import { ElMessage } from 'element-plus'
import Papa from 'papaparse'
import { useUserStore } from '@/store/modules/user'
import {
  Search, RefreshRight, Download, WarningFilled, CircleCheckFilled,
} from '@element-plus/icons-vue'

const userStore = useUserStore()

const historyList = ref([])
const tableLoading = ref(false)
const totalCount = ref(0)
const spamCount = ref(0)
const hamCount = ref(0)
const page = ref(1)
const pageSize = ref(20)

const filterLabel = ref('')
const dateRange = ref(null)

const detailVisible = ref(false)
const currentDetail = ref(null)

const dateShortcuts = [
  { text: '最近一周', value: () => { const e = new Date(); const s = new Date(); s.setDate(s.getDate() - 7); return [s, e] } },
  { text: '最近一月', value: () => { const e = new Date(); const s = new Date(); s.setMonth(s.getMonth() - 1); return [s, e] } },
  { text: '最近三月', value: () => { const e = new Date(); const s = new Date(); s.setMonth(s.getMonth() - 3); return [s, e] } },
]

function indexMethod(idx) {
  return (page.value - 1) * pageSize.value + idx + 1
}

function formatDateTime(dt) {
  if (!dt) return '--'
  const d = new Date(dt)
  const pad = (n) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`
}

function sortByConfidence(a, b) {
  return a.confidence - b.confidence
}

function sortByDate(a, b) {
  return new Date(a.created_at) - new Date(b.created_at)
}

function buildParams() {
  const params = {
    page: page.value,
    page_size: pageSize.value,
  }
  if (filterLabel.value) params.label = filterLabel.value
  if (dateRange.value && dateRange.value.length === 2) {
    params.start_date = dateRange.value[0]
    params.end_date = dateRange.value[1]
  }
  return params
}

async function fetchData() {
  tableLoading.value = true
  try {
    const params = buildParams()
    const [histRes, totalRes, spamRes, hamRes] = await Promise.all([
      getPredictionHistory(params),
      getPredictionCount(params),
      getPredictionCount({ ...params, label: 'spam' }),
      getPredictionCount({ ...params, label: 'ham' }),
    ])
    historyList.value = histRes.data
    totalCount.value = totalRes.data.count
    spamCount.value = spamRes.data.count
    hamCount.value = hamRes.data.count
  } catch {
    ElMessage.error('获取历史记录失败')
  } finally {
    tableLoading.value = false
  }
}

function handleSearch() {
  page.value = 1
  fetchData()
}

function handlePageChange() {
  fetchData()
}

function handleSizeChange() {
  page.value = 1
  fetchData()
}

function handleReset() {
  filterLabel.value = ''
  dateRange.value = null
  page.value = 1
  pageSize.value = 20
  fetchData()
}

function handleRowClick(row) {
  showDetail(row)
}

function showDetail(row) {
  currentDetail.value = row
  detailVisible.value = true
}

function handleExportCSV() {
  if (!historyList.value.length) return
  const exportData = historyList.value.map((row, idx) => ({
    '序号': indexMethod(idx),
    '邮件内容': row.input_text,
    '分类结果': row.prediction_label === 'spam' ? '垃圾邮件' : '正常邮件',
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
  a.download = `prediction_history_${new Date().toISOString().slice(0, 10)}.csv`
  a.click()
  URL.revokeObjectURL(url)
  ElMessage.success('CSV 导出成功')
}

onMounted(() => {
  fetchData()
})
</script>

<style scoped>
.history-page {
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

/* Filter */
.filter-card {
  padding: 16px 24px;
}
.filter-form {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 4px;
}
.filter-form :deep(.el-form-item) {
  margin-bottom: 0;
}

/* Mini stats */
.mini-stats {
  margin-bottom: 16px;
}
.mini-stat-card {
  background: rgba(255, 255, 255, 0.06);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 10px;
  padding: 16px 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.ms-spam { border-left: 3px solid #ef4444; }
.ms-ham { border-left: 3px solid #10b981; }
.ms-value {
  font-size: 22px;
  font-weight: 700;
  color: #ffffff;
}
.ms-spam .ms-value { color: #ef4444; }
.ms-ham .ms-value { color: #10b981; }
.ms-label {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.4);
}

/* Table */
.history-table :deep(.el-table__row) {
  cursor: pointer;
}
.text-preview {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.8);
}
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

/* Detail dialog */
.detail-dialog {
  padding: 0 8px;
}
.dd-result {
  text-align: center;
  padding: 24px;
  border-radius: 12px;
  margin-bottom: 20px;
}
.dd-spam {
  background: linear-gradient(135deg, #fef2f2, #fee2e2);
}
.dd-ham {
  background: linear-gradient(135deg, #f0fdf4, #dcfce7);
}
.dd-icon {
  margin-bottom: 8px;
}
.dd-spam .dd-icon { color: #ef4444; }
.dd-ham .dd-icon { color: #10b981; }
.dd-label {
  font-size: 22px;
  font-weight: 700;
  margin-bottom: 4px;
}
.dd-spam .dd-label { color: #ef4444; }
.dd-ham .dd-label { color: #10b981; }
.dd-confidence {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.55);
}

.dd-info-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
  margin-bottom: 20px;
}
.dd-info-item {
  background: rgba(255, 255, 255, 0.04);
  border-radius: 8px;
  padding: 12px 16px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.dd-info-label {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.4);
}
.dd-info-value {
  font-size: 14px;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.8);
}

.dd-text-section h4 {
  margin: 0 0 8px;
  font-size: 14px;
  font-weight: 600;
  color: #ffffff;
}
.dd-text-body {
  background: rgba(255, 255, 255, 0.04);
  border-radius: 10px;
  padding: 16px;
  font-size: 14px;
  line-height: 1.7;
  color: rgba(255, 255, 255, 0.8);
  max-height: 300px;
  overflow-y: auto;
  word-break: break-word;
}
</style>
