<template>
  <div class="dashboard-page">
    <!-- ========== 管理员控制台 ========== -->
    <template v-if="userStore.isAdmin">
      <div class="page-title-bar">
        <div>
          <h2>管理控制台</h2>
          <p class="page-desc">系统运行总览，快速掌控数据集、模型与预测状态</p>
        </div>
      </div>

      <el-row :gutter="16" class="stat-row" v-loading="loading">
        <el-col :span="6">
          <div class="stat-card">
            <div class="stat-icon" style="background: linear-gradient(135deg, #6366f1, #8b5cf6)">
              <el-icon :size="24"><Folder /></el-icon>
            </div>
            <div class="stat-body">
              <span class="stat-value">{{ overview.total_datasets }}</span>
              <span class="stat-label">数据集总数</span>
            </div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="stat-card">
            <div class="stat-icon" style="background: linear-gradient(135deg, #3b82f6, #06b6d4)">
              <el-icon :size="24"><DataAnalysis /></el-icon>
            </div>
            <div class="stat-body">
              <span class="stat-value">{{ overview.total_predictions }}</span>
              <span class="stat-label">预测总数</span>
            </div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="stat-card">
            <div class="stat-icon" style="background: linear-gradient(135deg, #ef4444, #f97316)">
              <el-icon :size="24"><WarningFilled /></el-icon>
            </div>
            <div class="stat-body">
              <span class="stat-value text-red">{{ overview.spam_predictions }}</span>
              <span class="stat-label">垃圾邮件</span>
            </div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="stat-card">
            <div class="stat-icon" style="background: linear-gradient(135deg, #10b981, #34d399)">
              <el-icon :size="24"><CircleCheckFilled /></el-icon>
            </div>
            <div class="stat-body">
              <span class="stat-value text-green">{{ overview.ham_predictions }}</span>
              <span class="stat-label">正常邮件</span>
            </div>
          </div>
        </el-col>
      </el-row>

      <!-- 快捷管理入口 -->
      <el-row :gutter="16" class="quick-row">
        <el-col :span="6" v-for="link in adminQuickLinks" :key="link.path">
          <div class="quick-card" @click="$router.push(link.path)">
            <el-icon :size="28" :style="{ color: link.color }"><component :is="link.icon" /></el-icon>
            <span class="quick-label">{{ link.label }}</span>
            <span class="quick-desc">{{ link.desc }}</span>
          </div>
        </el-col>
      </el-row>

      <el-row :gutter="16">
        <el-col :span="12">
          <div class="card">
            <h3 class="card-title">分类分布</h3>
            <PieChart :data="pieData" />
          </div>
        </el-col>
        <el-col :span="12">
          <div class="card">
            <div class="card-header">
              <h3 class="card-title">预测趋势 (近30天)</h3>
            </div>
            <LineChart :xData="trendDates" :series="trendSeries" />
          </div>
        </el-col>
      </el-row>

      <div class="card" v-if="modelComparison.length">
        <h3 class="card-title">已完成模型性能对比</h3>
        <BarChart
          :xData="modelComparison.map(m => m.name)"
          :series="modelBarSeries"
          height="320px"
        />
      </div>
    </template>

    <!-- ========== 普通用户首页 ========== -->
    <template v-else>
      <div class="page-title-bar">
        <div>
          <h2>欢迎回来，{{ userStore.username }}</h2>
          <p class="page-desc">快速检测邮件、查看预测结果与历史记录</p>
        </div>
      </div>

      <el-row :gutter="16" class="stat-row" v-loading="loading">
        <el-col :span="6">
          <div class="stat-card">
            <div class="stat-icon" style="background: linear-gradient(135deg, #3b82f6, #06b6d4)">
              <el-icon :size="24"><DataAnalysis /></el-icon>
            </div>
            <div class="stat-body">
              <span class="stat-value">{{ overview.total_predictions }}</span>
              <span class="stat-label">我的预测</span>
            </div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="stat-card">
            <div class="stat-icon" style="background: linear-gradient(135deg, #ef4444, #f97316)">
              <el-icon :size="24"><WarningFilled /></el-icon>
            </div>
            <div class="stat-body">
              <span class="stat-value text-red">{{ overview.spam_predictions }}</span>
              <span class="stat-label">垃圾邮件</span>
            </div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="stat-card">
            <div class="stat-icon" style="background: linear-gradient(135deg, #10b981, #34d399)">
              <el-icon :size="24"><CircleCheckFilled /></el-icon>
            </div>
            <div class="stat-body">
              <span class="stat-value text-green">{{ overview.ham_predictions }}</span>
              <span class="stat-label">正常邮件</span>
            </div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="stat-card">
            <div class="stat-icon" style="background: linear-gradient(135deg, #8b5cf6, #a855f7)">
              <el-icon :size="24"><Aim /></el-icon>
            </div>
            <div class="stat-body">
              <span class="stat-value text-purple">{{ (overview.avg_confidence * 100).toFixed(1) }}%</span>
              <span class="stat-label">平均置信度</span>
            </div>
          </div>
        </el-col>
      </el-row>

      <!-- 快捷操作卡片 -->
      <el-row :gutter="16" class="quick-row">
        <el-col :span="8">
          <div class="action-card" @click="$router.push('/predict')">
            <div class="action-icon" style="background: linear-gradient(135deg, #4f46e5, #7c3aed)">
              <el-icon :size="32"><Promotion /></el-icon>
            </div>
            <div class="action-body">
              <h4>快速检测</h4>
              <p>输入邮件内容，立即判断是否为垃圾邮件</p>
            </div>
            <el-icon class="action-arrow"><ArrowRight /></el-icon>
          </div>
        </el-col>
        <el-col :span="8">
          <div class="action-card" @click="$router.push('/predict/batch')">
            <div class="action-icon" style="background: linear-gradient(135deg, #3b82f6, #06b6d4)">
              <el-icon :size="32"><Files /></el-icon>
            </div>
            <div class="action-body">
              <h4>批量检测</h4>
              <p>选择数据集，对大量邮件进行批量分类预测</p>
            </div>
            <el-icon class="action-arrow"><ArrowRight /></el-icon>
          </div>
        </el-col>
        <el-col :span="8">
          <div class="action-card" @click="$router.push('/analysis')">
            <div class="action-icon" style="background: linear-gradient(135deg, #10b981, #34d399)">
              <el-icon :size="32"><TrendCharts /></el-icon>
            </div>
            <div class="action-body">
              <h4>结果分析</h4>
              <p>可视化查看预测数据分布与趋势变化</p>
            </div>
            <el-icon class="action-arrow"><ArrowRight /></el-icon>
          </div>
        </el-col>
      </el-row>

      <el-row :gutter="16">
        <el-col :span="12">
          <div class="card">
            <h3 class="card-title">分类分布</h3>
            <PieChart :data="pieData" />
          </div>
        </el-col>
        <el-col :span="12">
          <div class="card">
            <div class="card-header">
              <h3 class="card-title">预测趋势 (近30天)</h3>
            </div>
            <LineChart :xData="trendDates" :series="trendSeries" />
          </div>
        </el-col>
      </el-row>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, markRaw } from 'vue'
import { useUserStore } from '@/store/modules/user'
import { getOverview, getPredictionTrend, getModelComparison } from '@/api/analysis'
import {
  Folder, DataAnalysis, WarningFilled, CircleCheckFilled,
  Aim, Promotion, Files, TrendCharts, ArrowRight,
  User, Operation, Download, FolderOpened,
} from '@element-plus/icons-vue'
import PieChart from '@/components/charts/PieChart.vue'
import LineChart from '@/components/charts/LineChart.vue'
import BarChart from '@/components/charts/BarChart.vue'

const userStore = useUserStore()
const loading = ref(false)
const overview = ref({
  total_datasets: 0, total_predictions: 0,
  spam_predictions: 0, ham_predictions: 0, avg_confidence: 0,
})
const trendData = ref([])
const modelComparison = ref([])

const adminQuickLinks = [
  { path: '/admin/users', icon: markRaw(User), color: '#f59e0b', label: '用户管理', desc: '管理系统用户' },
  { path: '/admin/training', icon: markRaw(Operation), color: '#3b82f6', label: '模型训练', desc: '启动或监控训练' },
  { path: '/admin/export', icon: markRaw(Download), color: '#10b981', label: '模型导出', desc: '导出部署模型' },
  { path: '/admin/datasets', icon: markRaw(FolderOpened), color: '#8b5cf6', label: '数据集维护', desc: '清洗与维护数据' },
]

const pieData = computed(() => {
  if (!overview.value.total_predictions) return []
  return [
    { name: '垃圾邮件', value: overview.value.spam_predictions, itemStyle: { color: '#ef4444' } },
    { name: '正常邮件', value: overview.value.ham_predictions, itemStyle: { color: '#10b981' } },
  ]
})

const trendDates = computed(() => trendData.value.map(d => d.date))
const trendSeries = computed(() => [
  { name: '垃圾邮件', data: trendData.value.map(d => d.spam), itemStyle: { color: '#ef4444' } },
  { name: '正常邮件', data: trendData.value.map(d => d.ham), itemStyle: { color: '#10b981' } },
  { name: '总计', data: trendData.value.map(d => d.total), itemStyle: { color: '#6366f1' } },
])

const modelBarSeries = computed(() => [
  { name: '准确率', data: modelComparison.value.map(m => ((m.accuracy || 0) * 100).toFixed(2)), itemStyle: { color: '#3b82f6' } },
  { name: '精确率', data: modelComparison.value.map(m => ((m.precision || 0) * 100).toFixed(2)), itemStyle: { color: '#10b981' } },
  { name: '召回率', data: modelComparison.value.map(m => ((m.recall || 0) * 100).toFixed(2)), itemStyle: { color: '#f59e0b' } },
  { name: 'F1 分数', data: modelComparison.value.map(m => ((m.f1_score || 0) * 100).toFixed(2)), itemStyle: { color: '#8b5cf6' } },
])

async function fetchAll() {
  loading.value = true
  try {
    const promises = [getOverview(), getPredictionTrend(30)]
    if (userStore.isAdmin) promises.push(getModelComparison())

    const results = await Promise.all(promises)
    overview.value = results[0].data
    trendData.value = results[1].data
    if (results[2]) modelComparison.value = results[2].data
  } catch { /* silent */ } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchAll()
})
</script>

<style scoped>
.dashboard-page {
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

.stat-row {
  margin-bottom: 16px;
}
.stat-card {
  background: rgba(255, 255, 255, 0.06);
  border-radius: 12px;
  padding: 20px;
  display: flex;
  align-items: center;
  gap: 16px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
  border: 1px solid rgba(255, 255, 255, 0.08);
  backdrop-filter: blur(20px);
  transition: transform 0.2s;
}
.stat-card:hover {
  transform: translateY(-2px);
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

/* Quick links (admin) */
.quick-row {
  margin-bottom: 16px;
}
.quick-card {
  background: rgba(255, 255, 255, 0.06);
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
  border: 1px solid rgba(255, 255, 255, 0.08);
  backdrop-filter: blur(20px);
  cursor: pointer;
  transition: transform 0.2s, border-color 0.2s;
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}
.quick-card:hover {
  transform: translateY(-2px);
  border-color: rgba(99, 102, 241, 0.3);
}
.quick-label {
  font-size: 15px;
  font-weight: 600;
  color: #ffffff;
}
.quick-desc {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.35);
}

/* Action cards (user) */
.action-card {
  background: rgba(255, 255, 255, 0.06);
  border-radius: 12px;
  padding: 20px 24px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
  border: 1px solid rgba(255, 255, 255, 0.08);
  backdrop-filter: blur(20px);
  cursor: pointer;
  transition: transform 0.2s, border-color 0.2s;
  display: flex;
  align-items: center;
  gap: 16px;
}
.action-card:hover {
  transform: translateY(-2px);
  border-color: rgba(99, 102, 241, 0.3);
}
.action-icon {
  width: 56px;
  height: 56px;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  flex-shrink: 0;
}
.action-body {
  flex: 1;
  min-width: 0;
}
.action-body h4 {
  margin: 0 0 4px;
  font-size: 15px;
  font-weight: 600;
  color: #ffffff;
}
.action-body p {
  margin: 0;
  font-size: 12px;
  color: rgba(255, 255, 255, 0.35);
  line-height: 1.4;
}
.action-arrow {
  font-size: 18px;
  color: rgba(255, 255, 255, 0.2);
  flex-shrink: 0;
  transition: color 0.2s, transform 0.2s;
}
.action-card:hover .action-arrow {
  color: #a5b4fc;
  transform: translateX(4px);
}

.card {
  background: rgba(255, 255, 255, 0.06);
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
  border: 1px solid rgba(255, 255, 255, 0.08);
  backdrop-filter: blur(20px);
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
</style>
