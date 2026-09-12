<template>
  <div class="admin-export-page">
    <div class="page-title-bar">
      <div>
        <h2>模型导出</h2>
        <p class="page-desc">将已完成训练的模型导出为指定格式，支持 PyTorch 和 ONNX</p>
      </div>
    </div>

    <el-row :gutter="20">
      <el-col :span="10">
        <div class="card">
          <h3 class="card-title">
            <el-icon><Download /></el-icon>
            导出配置
          </h3>
          <el-form label-position="top">
            <el-form-item label="选择模型" required>
              <el-select v-model="selectedModelId" placeholder="选择已完成的模型" style="width: 100%" filterable :loading="modelsLoading">
                <el-option v-for="m in completedModels" :key="m.id" :label="`${m.name} (acc: ${m.accuracy ? (m.accuracy * 100).toFixed(1) + '%' : '--'})`" :value="m.id" />
              </el-select>
            </el-form-item>
            <el-form-item label="导出格式">
              <el-radio-group v-model="exportFormat">
                <el-radio-button value="pytorch">PyTorch (.pt)</el-radio-button>
                <el-radio-button value="onnx">ONNX (.onnx)</el-radio-button>
              </el-radio-group>
            </el-form-item>
            <el-button type="primary" class="export-btn" size="large" :loading="exporting" :disabled="!selectedModelId" @click="handleExport">
              <el-icon><Upload /></el-icon>
              导出模型
            </el-button>
          </el-form>

          <div v-if="exportResult" class="export-result">
            <el-result icon="success" title="导出成功" :sub-title="exportResult.message">
              <template #extra>
                <el-button type="primary" @click="handleDownload">
                  <el-icon><Download /></el-icon>
                  下载模型文件
                </el-button>
              </template>
            </el-result>
          </div>
        </div>
      </el-col>

      <el-col :span="14">
        <div class="card">
          <h3 class="card-title">
            <el-icon><Cpu /></el-icon>
            可导出模型列表
          </h3>
          <el-table :data="completedModels" stripe border size="small" v-loading="modelsLoading">
            <el-table-column prop="id" label="ID" width="60" align="center" />
            <el-table-column prop="name" label="模型名称" min-width="160">
              <template #default="{ row }">
                {{ row.name }}
                <el-tag v-if="row.is_active" type="success" size="small" style="margin-left: 4px">激活</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="准确率" width="90" align="center">
              <template #default="{ row }">{{ row.accuracy ? (row.accuracy * 100).toFixed(2) + '%' : '--' }}</template>
            </el-table-column>
            <el-table-column label="F1" width="90" align="center">
              <template #default="{ row }">{{ row.f1_score ? (row.f1_score * 100).toFixed(2) + '%' : '--' }}</template>
            </el-table-column>
            <el-table-column label="已导出格式" width="120" align="center">
              <template #default="{ row }">
                <el-tag v-if="row.exported_format" size="small">{{ row.exported_format }}</el-tag>
                <span v-else style="color: #9ca3af">未导出</span>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="100" align="center">
              <template #default="{ row }">
                <el-button link type="primary" size="small" @click="selectedModelId = row.id">选择</el-button>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { getModels, exportModel, downloadModel } from '@/api/model'
import { ElMessage } from 'element-plus'
import { Download, Upload, Cpu } from '@element-plus/icons-vue'

const modelsLoading = ref(false)
const models = ref([])
const selectedModelId = ref(null)
const exportFormat = ref('pytorch')
const exporting = ref(false)
const exportResult = ref(null)

const completedModels = computed(() => models.value.filter(m => m.status === 'completed'))

async function fetchModels() {
  modelsLoading.value = true
  try {
    const res = await getModels()
    models.value = res.data
  } catch { /* silent */ } finally {
    modelsLoading.value = false
  }
}

async function handleExport() {
  if (!selectedModelId.value) return
  exporting.value = true
  exportResult.value = null
  try {
    const res = await exportModel({
      model_id: selectedModelId.value,
      export_format: exportFormat.value,
    })
    exportResult.value = res.data
    ElMessage.success('模型导出成功')
    fetchModels()
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || '导出失败')
  } finally {
    exporting.value = false
  }
}

async function handleDownload() {
  if (!selectedModelId.value) return
  try {
    const res = await downloadModel(selectedModelId.value, exportFormat.value)
    const blob = new Blob([res.data], { type: 'application/zip' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `model_${selectedModelId.value}_${exportFormat.value}.zip`
    a.click()
    URL.revokeObjectURL(url)
    ElMessage.success('下载已开始')
  } catch {
    ElMessage.error('下载失败')
  }
}

onMounted(() => {
  fetchModels()
})
</script>

<style scoped>
.admin-export-page {
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
.export-btn {
  width: 100%;
  border-radius: 10px;
  font-weight: 600;
  background: linear-gradient(135deg, #4f46e5, #7c3aed);
  border: none;
  margin-top: 8px;
}
.export-result {
  margin-top: 20px;
  padding: 16px;
  background: rgba(16, 185, 129, 0.1);
  border-radius: 10px;
}
</style>
