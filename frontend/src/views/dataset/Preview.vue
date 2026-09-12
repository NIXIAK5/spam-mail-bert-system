<template>
  <div class="preview-page">
    <!-- 返回 + 标题 -->
    <div class="page-title-bar">
      <div class="title-left">
        <el-button text @click="router.push('/dataset')">
          <el-icon><ArrowLeft /></el-icon>
          返回列表
        </el-button>
        <div>
          <h2>{{ dataset?.name || '数据集预览' }}</h2>
          <p class="page-desc">{{ dataset?.description || '查看数据样本与统计信息' }}</p>
        </div>
      </div>
      <el-tag :type="dataset?.status === 'processed' ? 'success' : 'warning'" size="large">
        {{ dataset?.status === 'processed' ? '已处理' : '待处理' }}
      </el-tag>
    </div>

    <!-- 统计概览 -->
    <el-row :gutter="16" class="stat-row" v-loading="statsLoading">
      <el-col :span="6">
        <div class="stat-card">
          <div class="stat-icon" style="background: linear-gradient(135deg, #6366f1, #8b5cf6)">
            <el-icon :size="22"><Document /></el-icon>
          </div>
          <div class="stat-info">
            <span class="stat-value">{{ stats.total_samples?.toLocaleString() || 0 }}</span>
            <span class="stat-label">总样本数</span>
          </div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="stat-card">
          <div class="stat-icon" style="background: linear-gradient(135deg, #ef4444, #f97316)">
            <el-icon :size="22"><Warning /></el-icon>
          </div>
          <div class="stat-info">
            <span class="stat-value">{{ stats.spam_count?.toLocaleString() || 0 }}</span>
            <span class="stat-label">垃圾邮件</span>
          </div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="stat-card">
          <div class="stat-icon" style="background: linear-gradient(135deg, #10b981, #34d399)">
            <el-icon :size="22"><CircleCheck /></el-icon>
          </div>
          <div class="stat-info">
            <span class="stat-value">{{ stats.ham_count?.toLocaleString() || 0 }}</span>
            <span class="stat-label">正常邮件</span>
          </div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="stat-card">
          <div class="stat-icon" style="background: linear-gradient(135deg, #3b82f6, #06b6d4)">
            <el-icon :size="22"><DataAnalysis /></el-icon>
          </div>
          <div class="stat-info">
            <span class="stat-value">{{ spamRatioText }}</span>
            <span class="stat-label">垃圾邮件比例</span>
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- 饼图 + 信息 -->
    <el-row :gutter="16" class="chart-row">
      <el-col :span="12">
        <div class="card">
          <h3 class="card-title">邮件类型分布</h3>
          <PieChart :data="pieData" title="" style="height: 320px" />
        </div>
      </el-col>
      <el-col :span="12">
        <div class="card info-card">
          <h3 class="card-title">数据集信息</h3>
          <el-descriptions :column="1" border>
            <el-descriptions-item label="数据集ID">{{ dataset?.id }}</el-descriptions-item>
            <el-descriptions-item label="名称">{{ dataset?.name }}</el-descriptions-item>
            <el-descriptions-item label="文件格式">
              <el-tag size="small">{{ dataset?.file_format?.toUpperCase() }}</el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="数据集类型">
              <el-tag size="small" :type="dataset?.type === 'train' ? 'success' : 'info'">
                {{ dataset?.type === 'train' ? '训练集' : '测试集' }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="公开">
              {{ dataset?.is_public ? '是' : '否' }}
            </el-descriptions-item>
            <el-descriptions-item label="版本">{{ dataset?.version || '1.0' }}</el-descriptions-item>
            <el-descriptions-item label="上传时间">{{ formatDate(dataset?.upload_time) }}</el-descriptions-item>
          </el-descriptions>
        </div>
      </el-col>
    </el-row>

    <!-- 数据预览表 -->
    <div class="card">
      <div class="card-header">
        <h3 class="card-title">样本预览</h3>
        <el-select v-model="previewRows" style="width: 130px" @change="fetchPreview">
          <el-option :value="10" label="前 10 条" />
          <el-option :value="20" label="前 20 条" />
          <el-option :value="50" label="前 50 条" />
          <el-option :value="100" label="前 100 条" />
        </el-select>
      </div>
      <el-table
        :data="preview.sample_data"
        v-loading="previewLoading"
        stripe
        border
        max-height="500"
        style="width: 100%"
      >
        <el-table-column type="index" label="#" width="60" align="center" />
        <el-table-column
          v-for="col in preview.columns"
          :key="col"
          :prop="col"
          :label="col"
          min-width="160"
          show-overflow-tooltip
        >
          <template #default="{ row }">
            <template v-if="col === 'label' || col === 'Label' || col === '标签'">
              <el-tag
                :type="Number(row[col]) === 1 ? 'danger' : 'success'"
                size="small"
              >
                {{ Number(row[col]) === 1 ? '垃圾' : '正常' }}
              </el-tag>
            </template>
            <template v-else>{{ row[col] }}</template>
          </template>
        </el-table-column>
      </el-table>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getDataset, previewDataset, getDatasetStats } from '@/api/dataset'
import { ElMessage } from 'element-plus'
import {
  ArrowLeft, Document, Warning, CircleCheck, DataAnalysis,
} from '@element-plus/icons-vue'
import PieChart from '@/components/charts/PieChart.vue'

const route = useRoute()
const router = useRouter()
const datasetId = Number(route.params.id)

const dataset = ref(null)
const stats = ref({})
const statsLoading = ref(false)
const preview = ref({ columns: [], sample_data: [] })
const previewLoading = ref(false)
const previewRows = ref(10)

const spamRatioText = computed(() => {
  const r = stats.value.spam_ratio
  return r != null ? `${(r * 100).toFixed(1)}%` : '--'
})

const pieData = computed(() => {
  if (!stats.value.spam_count && !stats.value.ham_count) return []
  return [
    { name: '垃圾邮件', value: stats.value.spam_count || 0, itemStyle: { color: '#ef4444' } },
    { name: '正常邮件', value: stats.value.ham_count || 0, itemStyle: { color: '#10b981' } },
  ]
})

function formatDate(dateStr) {
  if (!dateStr) return '--'
  const d = new Date(dateStr)
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')} ${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
}

async function fetchDataset() {
  try {
    const res = await getDataset(datasetId)
    dataset.value = res.data
  } catch {
    ElMessage.error('获取数据集信息失败')
  }
}

async function fetchStats() {
  statsLoading.value = true
  try {
    const res = await getDatasetStats(datasetId)
    stats.value = res.data
  } catch {
    ElMessage.error('获取统计信息失败')
  } finally {
    statsLoading.value = false
  }
}

async function fetchPreview() {
  previewLoading.value = true
  try {
    const res = await previewDataset(datasetId, previewRows.value)
    preview.value = res.data
  } catch {
    ElMessage.error('获取预览数据失败')
  } finally {
    previewLoading.value = false
  }
}

onMounted(() => {
  fetchDataset()
  fetchStats()
  fetchPreview()
})
</script>

<style scoped>
.preview-page {
  max-width: 1200px;
  margin: 0 auto;
}

.page-title-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
}
.title-left {
  display: flex;
  align-items: center;
  gap: 12px;
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

/* Stat cards */
.stat-row {
  margin-bottom: 20px;
}
.stat-card {
  background: rgba(255, 255, 255, 0.06);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 12px;
  padding: 20px;
  display: flex;
  align-items: center;
  gap: 14px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
}
.stat-icon {
  width: 44px;
  height: 44px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  flex-shrink: 0;
}
.stat-info {
  display: flex;
  flex-direction: column;
}
.stat-value {
  font-size: 20px;
  font-weight: 700;
  color: #ffffff;
}
.stat-label {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.4);
}

/* Cards */
.card {
  background: rgba(255, 255, 255, 0.06);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
  margin-bottom: 16px;
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
  color: #ffffff;
}
.card-header .card-title {
  margin-bottom: 0;
}

.chart-row {
  margin-bottom: 4px;
}
.info-card .card-title {
  margin-bottom: 16px;
}
</style>
