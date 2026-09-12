<template>
  <div class="admin-datasets-page">
    <div class="page-title-bar">
      <div>
        <h2>数据集维护</h2>
        <p class="page-desc">管理数据集、执行数据清洗操作</p>
      </div>
      <el-button type="primary" class="action-btn" @click="showUploadDialog = true">
        <el-icon><Upload /></el-icon>
        上传数据集
      </el-button>
    </div>

    <div class="card">
      <el-table :data="datasets" stripe border v-loading="loading" size="default">
        <el-table-column prop="id" label="ID" width="70" align="center" />
        <el-table-column prop="name" label="名称" min-width="160" />
        <el-table-column label="格式" width="80" align="center">
          <template #default="{ row }">
            <el-tag size="small" :type="row.file_format === 'csv' ? '' : 'warning'">
              {{ row.file_format?.toUpperCase() }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="类型" width="90" align="center">
          <template #default="{ row }">
            <el-tag size="small" :type="row.type === 'train' ? 'success' : 'info'">
              {{ row.type === 'train' ? '训练集' : '测试集' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="total_samples" label="样本数" width="100" align="center" />
        <el-table-column label="垃圾/正常" width="120" align="center">
          <template #default="{ row }">
            <span style="color: #ef4444">{{ row.spam_count }}</span> / <span style="color: #10b981">{{ row.ham_count }}</span>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="90" align="center">
          <template #default="{ row }">
            <el-tag size="small" :type="row.status === 'processed' ? 'success' : 'warning'">
              {{ row.status === 'processed' ? '已处理' : '待处理' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="公开" width="70" align="center">
          <template #default="{ row }">{{ row.is_public ? '是' : '否' }}</template>
        </el-table-column>
        <el-table-column label="操作" width="200" align="center" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click="$router.push(`/dataset/${row.id}/preview`)">预览</el-button>
            <el-button link type="warning" size="small" @click="openCleanDialog(row)">清洗</el-button>
            <el-button link type="danger" size="small" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- 上传对话框 -->
    <el-dialog v-model="showUploadDialog" title="上传数据集" width="520px" destroy-on-close>
      <el-form :model="uploadForm" label-position="top">
        <el-form-item label="数据集名称" required>
          <el-input v-model="uploadForm.name" placeholder="请输入名称" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="uploadForm.description" type="textarea" :rows="2" />
        </el-form-item>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="类型">
              <el-select v-model="uploadForm.type" style="width: 100%">
                <el-option label="训练集" value="train" />
                <el-option label="测试集" value="test" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="公开可见">
              <el-switch v-model="uploadForm.is_public" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="选择文件">
          <el-upload :auto-upload="false" :limit="1" accept=".csv,.txt" :on-change="f => uploadForm.file = f.raw" drag>
            <el-icon :size="40" style="color: #9ca3af"><UploadFilled /></el-icon>
            <div class="el-upload__text">拖拽或<em>点击上传</em></div>
            <template #tip><div class="el-upload__tip">支持 CSV / TXT</div></template>
          </el-upload>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showUploadDialog = false">取消</el-button>
        <el-button type="primary" :loading="uploading" @click="handleUpload">上传</el-button>
      </template>
    </el-dialog>

    <!-- 清洗对话框 -->
    <el-dialog v-model="cleanDialogVisible" title="数据清洗" width="480px" destroy-on-close>
      <p style="margin: 0 0 16px; color: #6b7280;">
        对数据集「<strong>{{ cleanTarget?.name }}</strong>」执行以下清洗操作：
      </p>
      <el-form label-position="left" label-width="140px">
        <el-form-item label="去除重复行">
          <el-switch v-model="cleanOptions.remove_duplicates" />
        </el-form-item>
        <el-form-item label="填充缺失值">
          <el-switch v-model="cleanOptions.fill_missing" />
        </el-form-item>
        <el-form-item label="去除首尾空格">
          <el-switch v-model="cleanOptions.strip_whitespace" />
        </el-form-item>
        <el-form-item label="删除空行">
          <el-switch v-model="cleanOptions.remove_empty_rows" />
        </el-form-item>
      </el-form>
      <div v-if="cleanResult" class="clean-result">
        <el-descriptions :column="2" border size="small">
          <el-descriptions-item label="原始行数">{{ cleanResult.original_rows }}</el-descriptions-item>
          <el-descriptions-item label="清洗后行数">{{ cleanResult.cleaned_rows }}</el-descriptions-item>
          <el-descriptions-item label="删除行数">{{ cleanResult.removed_rows }}</el-descriptions-item>
          <el-descriptions-item label="去重行数">{{ cleanResult.duplicates_removed }}</el-descriptions-item>
          <el-descriptions-item label="缺失值填充">{{ cleanResult.missing_filled }}</el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag type="success" size="small">{{ cleanResult.status }}</el-tag>
          </el-descriptions-item>
        </el-descriptions>
      </div>
      <template #footer>
        <el-button @click="cleanDialogVisible = false">关闭</el-button>
        <el-button type="primary" :loading="cleaning" @click="handleClean" :disabled="!!cleanResult">
          执行清洗
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getDatasets, uploadDataset, cleanDataset, deleteDataset } from '@/api/dataset'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Upload, UploadFilled } from '@element-plus/icons-vue'

const loading = ref(false)
const datasets = ref([])
const showUploadDialog = ref(false)
const uploading = ref(false)

const uploadForm = ref({ name: '', description: '', type: 'train', is_public: false, file: null })

const cleanDialogVisible = ref(false)
const cleanTarget = ref(null)
const cleaning = ref(false)
const cleanResult = ref(null)
const cleanOptions = ref({
  remove_duplicates: true,
  fill_missing: true,
  strip_whitespace: true,
  remove_empty_rows: true,
})

async function fetchDatasets() {
  loading.value = true
  try {
    const res = await getDatasets()
    datasets.value = res.data
  } catch {
    ElMessage.error('获取数据集列表失败')
  } finally {
    loading.value = false
  }
}

async function handleUpload() {
  if (!uploadForm.value.name || !uploadForm.value.file) {
    ElMessage.warning('请填写名称并选择文件')
    return
  }
  const fd = new FormData()
  fd.append('file', uploadForm.value.file)
  fd.append('name', uploadForm.value.name)
  fd.append('description', uploadForm.value.description)
  fd.append('type', uploadForm.value.type)
  fd.append('is_public', uploadForm.value.is_public)
  uploading.value = true
  try {
    await uploadDataset(fd)
    ElMessage.success('上传成功')
    showUploadDialog.value = false
    uploadForm.value = { name: '', description: '', type: 'train', is_public: false, file: null }
    fetchDatasets()
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || '上传失败')
  } finally {
    uploading.value = false
  }
}

function openCleanDialog(row) {
  cleanTarget.value = row
  cleanResult.value = null
  cleanOptions.value = {
    remove_duplicates: true,
    fill_missing: true,
    strip_whitespace: true,
    remove_empty_rows: true,
  }
  cleanDialogVisible.value = true
}

async function handleClean() {
  if (!cleanTarget.value) return
  cleaning.value = true
  try {
    const res = await cleanDataset(cleanTarget.value.id, cleanOptions.value)
    cleanResult.value = res.data
    ElMessage.success('数据清洗完成')
    fetchDatasets()
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || '清洗失败')
  } finally {
    cleaning.value = false
  }
}

async function handleDelete(row) {
  await ElMessageBox.confirm(`确认删除数据集「${row.name}」？`, '删除确认', { type: 'warning' })
  try {
    await deleteDataset(row.id)
    ElMessage.success('删除成功')
    fetchDatasets()
  } catch {
    ElMessage.error('删除失败')
  }
}

onMounted(() => {
  fetchDatasets()
})
</script>

<style scoped>
.admin-datasets-page {
  max-width: 1200px;
  margin: 0 auto;
}
.page-title-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
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
.action-btn {
  border-radius: 10px;
  font-weight: 600;
  background: linear-gradient(135deg, #4f46e5, #7c3aed);
  border: none;
}
.card {
  background: rgba(255, 255, 255, 0.06);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
}
.clean-result {
  margin-top: 16px;
  padding: 16px;
  background: rgba(16, 185, 129, 0.1);
  border-radius: 8px;
}
</style>
