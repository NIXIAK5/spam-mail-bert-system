<template>
  <div class="dataset-page">
    <div class="page-title-bar">
      <div>
        <h2>{{ userStore.isAdmin ? '数据集管理' : '数据浏览' }}</h2>
        <p class="page-desc">{{ userStore.isAdmin ? '上传、管理和预览垃圾邮件分类数据集' : '浏览可用的数据集，查看样本分布与详细数据' }}</p>
      </div>
      <el-button v-if="userStore.isAdmin" type="primary" class="upload-btn" @click="showUploadDialog = true">
        <el-icon><Upload /></el-icon>
        上传数据集
      </el-button>
    </div>

    <!-- 统计卡片 -->
    <el-row :gutter="16" class="stat-row">
      <el-col :span="6">
        <div class="stat-card">
          <div class="stat-icon" style="background: linear-gradient(135deg, #6366f1, #8b5cf6)">
            <el-icon :size="24"><Folder /></el-icon>
          </div>
          <div class="stat-info">
            <span class="stat-value">{{ datasets.length }}</span>
            <span class="stat-label">数据集总数</span>
          </div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="stat-card">
          <div class="stat-icon" style="background: linear-gradient(135deg, #3b82f6, #06b6d4)">
            <el-icon :size="24"><Document /></el-icon>
          </div>
          <div class="stat-info">
            <span class="stat-value">{{ totalSamples.toLocaleString() }}</span>
            <span class="stat-label">样本总量</span>
          </div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="stat-card">
          <div class="stat-icon" style="background: linear-gradient(135deg, #ef4444, #f97316)">
            <el-icon :size="24"><Warning /></el-icon>
          </div>
          <div class="stat-info">
            <span class="stat-value">{{ totalSpam.toLocaleString() }}</span>
            <span class="stat-label">垃圾邮件</span>
          </div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="stat-card">
          <div class="stat-icon" style="background: linear-gradient(135deg, #10b981, #34d399)">
            <el-icon :size="24"><CircleCheck /></el-icon>
          </div>
          <div class="stat-info">
            <span class="stat-value">{{ totalHam.toLocaleString() }}</span>
            <span class="stat-label">正常邮件</span>
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- 数据集列表 -->
    <div class="table-card">
      <el-table :data="datasets" v-loading="loading" stripe style="width: 100%">
        <el-table-column v-if="userStore.isAdmin" prop="id" label="ID" width="70" align="center" />
        <el-table-column prop="name" label="名称" min-width="180">
          <template #default="{ row }">
            <span class="dataset-name" @click="goPreview(row.id)">{{ row.name }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="description" label="描述" min-width="200" show-overflow-tooltip />
        <el-table-column v-if="userStore.isAdmin" label="格式" width="80" align="center">
          <template #default="{ row }">
            <el-tag size="small" :type="row.file_format === 'csv' ? '' : 'warning'">
              {{ row.file_format?.toUpperCase() }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column v-if="userStore.isAdmin" label="类型" width="90" align="center">
          <template #default="{ row }">
            <el-tag size="small" :type="row.type === 'train' ? 'success' : 'info'">
              {{ row.type === 'train' ? '训练集' : '测试集' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="total_samples" label="样本数" width="100" align="center" />
        <el-table-column label="垃圾/正常" width="120" align="center">
          <template #default="{ row }">
            <span style="color: #ef4444">{{ row.spam_count }}</span>
            /
            <span style="color: #10b981">{{ row.ham_count }}</span>
          </template>
        </el-table-column>
        <el-table-column v-if="userStore.isAdmin" label="状态" width="90" align="center">
          <template #default="{ row }">
            <el-tag size="small" :type="row.status === 'processed' ? 'success' : 'warning'">
              {{ row.status === 'processed' ? '已处理' : '待处理' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="上传时间" width="170" align="center">
          <template #default="{ row }">
            {{ formatDate(row.upload_time) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" :width="userStore.isAdmin ? 160 : 80" align="center" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="goPreview(row.id)">预览</el-button>
            <el-button
              v-if="userStore.isAdmin"
              link type="danger"
              @click="handleDelete(row)"
            >删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- 上传对话框 -->
    <el-dialog
      v-model="showUploadDialog"
      title="上传数据集"
      width="560px"
      destroy-on-close
      @close="resetUploadForm"
    >
      <el-form
        ref="uploadFormRef"
        :model="uploadForm"
        :rules="uploadRules"
        label-position="top"
      >
        <el-form-item label="数据集名称" prop="name">
          <el-input v-model="uploadForm.name" placeholder="请输入数据集名称" />
        </el-form-item>
        <el-form-item label="描述" prop="description">
          <el-input
            v-model="uploadForm.description"
            type="textarea"
            :rows="2"
            placeholder="简要描述该数据集"
          />
        </el-form-item>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="数据集类型" prop="type">
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
        <el-form-item label="选择文件" prop="file">
          <el-upload
            ref="uploadRef"
            :auto-upload="false"
            :limit="1"
            accept=".csv,.txt"
            :on-change="handleFileChange"
            :on-remove="handleFileRemove"
            drag
          >
            <el-icon :size="40" class="upload-icon"><UploadFilled /></el-icon>
            <div class="el-upload__text">将文件拖到此处，或<em>点击上传</em></div>
            <template #tip>
              <div class="el-upload__tip">仅支持 CSV / TXT 格式文件</div>
            </template>
          </el-upload>
        </el-form-item>

        <!-- 文件预览 -->
        <div v-if="previewData.length" class="file-preview">
          <h4>文件预览（前 5 行）</h4>
          <el-table :data="previewData" size="small" max-height="200" border>
            <el-table-column
              v-for="col in previewColumns"
              :key="col"
              :prop="col"
              :label="col"
              min-width="120"
              show-overflow-tooltip
            />
          </el-table>
        </div>
      </el-form>

      <template #footer>
        <el-button @click="showUploadDialog = false">取消</el-button>
        <el-button type="primary" :loading="uploading" @click="handleUpload">
          确认上传
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/store/modules/user'
import { getDatasets, uploadDataset, deleteDataset } from '@/api/dataset'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Upload, UploadFilled, Folder, Document, Warning,
  CircleCheck,
} from '@element-plus/icons-vue'
import Papa from 'papaparse'

const router = useRouter()
const userStore = useUserStore()

const loading = ref(false)
const datasets = ref([])
const showUploadDialog = ref(false)
const uploading = ref(false)
const uploadFormRef = ref(null)
const uploadRef = ref(null)

const uploadForm = ref({
  name: '',
  description: '',
  type: 'train',
  is_public: false,
  file: null,
})

const uploadRules = {
  name: [{ required: true, message: '请输入数据集名称', trigger: 'blur' }],
}

const previewColumns = ref([])
const previewData = ref([])

const totalSamples = computed(() => datasets.value.reduce((s, d) => s + (d.total_samples || 0), 0))
const totalSpam = computed(() => datasets.value.reduce((s, d) => s + (d.spam_count || 0), 0))
const totalHam = computed(() => datasets.value.reduce((s, d) => s + (d.ham_count || 0), 0))

function formatDate(dateStr) {
  if (!dateStr) return '--'
  const d = new Date(dateStr)
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')} ${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
}

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

function goPreview(id) {
  router.push(`/dataset/${id}/preview`)
}

function handleFileChange(file) {
  uploadForm.value.file = file.raw
  parseLocalFile(file.raw)
}

function handleFileRemove() {
  uploadForm.value.file = null
  previewColumns.value = []
  previewData.value = []
}

function parseLocalFile(file) {
  const reader = new FileReader()
  reader.onload = (e) => {
    const text = e.target.result
    const isTab = file.name.endsWith('.txt')
    const parsed = Papa.parse(text, { header: true, delimiter: isTab ? '\t' : ',', preview: 5 })
    if (parsed.meta.fields?.length) {
      previewColumns.value = parsed.meta.fields
      previewData.value = parsed.data
    }
  }
  reader.readAsText(file)
}

function resetUploadForm() {
  uploadForm.value = { name: '', description: '', type: 'train', is_public: false, file: null }
  previewColumns.value = []
  previewData.value = []
}

async function handleUpload() {
  await uploadFormRef.value.validate()
  if (!uploadForm.value.file) {
    ElMessage.warning('请选择要上传的文件')
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
    ElMessage.success('数据集上传成功')
    showUploadDialog.value = false
    fetchDatasets()
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || '上传失败')
  } finally {
    uploading.value = false
  }
}

async function handleDelete(row) {
  await ElMessageBox.confirm(`确认删除数据集「${row.name}」？此操作不可撤销。`, '删除确认', {
    type: 'warning',
    confirmButtonText: '删除',
    cancelButtonText: '取消',
  })
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
.dataset-page {
  max-width: 1200px;
  margin: 0 auto;
}

.page-title-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
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
.upload-btn {
  border-radius: 10px;
  font-weight: 600;
  padding: 0 24px;
  height: 40px;
  background: linear-gradient(135deg, #4f46e5, #7c3aed);
  border: none;
}
.upload-btn:hover {
  background: linear-gradient(135deg, #4338ca, #6d28d9);
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
  gap: 16px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
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
.stat-info {
  display: flex;
  flex-direction: column;
}
.stat-value {
  font-size: 22px;
  font-weight: 700;
  color: #ffffff;
}
.stat-label {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.4);
}

/* Table card */
.table-card {
  background: rgba(255, 255, 255, 0.06);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
}

.dataset-name {
  color: #818cf8;
  cursor: pointer;
  font-weight: 500;
}
.dataset-name:hover {
  text-decoration: underline;
}

/* Upload dialog */
.upload-icon {
  color: rgba(255, 255, 255, 0.4);
}
.file-preview {
  margin-top: 12px;
}
.file-preview h4 {
  margin: 0 0 8px;
  font-size: 14px;
  color: rgba(255, 255, 255, 0.8);
}
</style>
