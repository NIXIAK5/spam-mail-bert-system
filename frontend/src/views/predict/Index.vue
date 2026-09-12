<template>
  <div class="predict-page">
    <div class="page-title-bar">
      <div>
        <h2>{{ userStore.isAdmin ? '模型预测' : '邮件检测' }}</h2>
        <p class="page-desc">{{ userStore.isAdmin ? '输入邮件文本内容，使用 AI 模型判断是否为垃圾邮件' : '粘贴或输入邮件内容，一键智能识别是否为垃圾邮件' }}</p>
      </div>
    </div>

    <el-row :gutter="20">
      <!-- 输入区域 -->
      <el-col :span="14">
        <div class="card input-card">
          <h3 class="card-title">
            <el-icon><EditPen /></el-icon>
            输入邮件内容
          </h3>
          <el-input
            v-model="emailText"
            type="textarea"
            :rows="10"
            placeholder="请在此输入或粘贴邮件文本内容..."
            resize="vertical"
            class="email-textarea"
          />
          <div class="input-actions">
            <span class="char-count">{{ emailText.length }} 个字符</span>
            <div>
              <el-button @click="fillExample('spam')">填入垃圾邮件示例</el-button>
              <el-button @click="fillExample('ham')">填入正常邮件示例</el-button>
              <el-button @click="emailText = ''">清空</el-button>
              <el-button
                type="primary"
                class="predict-btn"
                :loading="predicting"
                :disabled="!emailText.trim()"
                @click="handlePredict"
              >
                <el-icon><Promotion /></el-icon>
                开始预测
              </el-button>
            </div>
          </div>
        </div>
      </el-col>

      <!-- 结果区域 -->
      <el-col :span="10">
        <div class="card result-card" :class="resultClass">
          <h3 class="card-title">
            <el-icon><DataAnalysis /></el-icon>
            预测结果
          </h3>

          <template v-if="result">
            <div class="result-main">
              <div class="result-icon-wrapper" :class="result.label === 'spam' ? 'icon-spam' : 'icon-ham'">
                <el-icon :size="48">
                  <WarningFilled v-if="result.label === 'spam'" />
                  <CircleCheckFilled v-else />
                </el-icon>
              </div>
              <div class="result-label" :class="result.label === 'spam' ? 'label-spam' : 'label-ham'">
                {{ result.label === 'spam' ? '垃圾邮件' : '正常邮件' }}
              </div>
            </div>

            <!-- 置信度 -->
            <div class="confidence-section">
              <div class="confidence-header">
                <span>置信度</span>
                <span class="confidence-value">{{ (result.confidence * 100).toFixed(1) }}%</span>
              </div>
              <el-progress
                :percentage="Number((result.confidence * 100).toFixed(1))"
                :color="result.label === 'spam' ? '#ef4444' : '#10b981'"
                :stroke-width="12"
                :show-text="false"
              />
            </div>

            <!-- 详细信息 -->
            <div class="result-details">
              <div class="detail-item">
                <span class="detail-label">处理耗时</span>
                <span class="detail-value">{{ result.processing_time }}s</span>
              </div>
              <div class="detail-item">
                <span class="detail-label">判定类别</span>
                <el-tag
                  :type="result.label === 'spam' ? 'danger' : 'success'"
                  size="small"
                >{{ result.label }}</el-tag>
              </div>
              <div class="detail-item">
                <span class="detail-label">文本长度</span>
                <span class="detail-value">{{ emailText.length }} 字</span>
              </div>
            </div>

            <!-- 用户反馈 -->
            <div class="feedback-section">
              <p class="feedback-label">结果是否准确？</p>
              <div v-if="feedbackSubmitted" class="feedback-done">
                <el-icon color="#10b981"><CircleCheckFilled /></el-icon>
                <span>感谢您的反馈！</span>
              </div>
              <div v-else class="feedback-btns">
                <el-button
                  size="small"
                  class="btn-correct"
                  :loading="feedbackLoading"
                  @click="handleFeedback(true)"
                >
                  <el-icon><Select /></el-icon> 结果正确
                </el-button>
                <el-button
                  size="small"
                  class="btn-wrong"
                  :loading="feedbackLoading"
                  @click="showWrongDialog = true"
                >
                  <el-icon><CloseBold /></el-icon> 结果错误
                </el-button>
              </div>
            </div>
          </template>

          <template v-else>
            <div class="result-empty">
              <el-icon :size="64" color="#e5e7eb"><ChatDotRound /></el-icon>
              <p>输入邮件内容并点击「开始预测」<br>即可查看分类结果</p>
            </div>
          </template>
        </div>

        <!-- 反馈：结果错误弹窗 -->
        <el-dialog v-model="showWrongDialog" title="结果错误 - 请告知正确分类" width="360px" align-center>
          <p style="color: rgba(255,255,255,0.6); margin: 0 0 16px; font-size: 13px;">
            您认为该邮件的正确分类是？（可选，帮助模型改进）
          </p>
          <el-radio-group v-model="wrongCorrectLabel" style="display:flex; gap:12px;">
            <el-radio value="spam">垃圾邮件 (spam)</el-radio>
            <el-radio value="ham">正常邮件 (ham)</el-radio>
          </el-radio-group>
          <template #footer>
            <el-button @click="showWrongDialog = false">取消</el-button>
            <el-button type="danger" :loading="feedbackLoading" @click="handleFeedback(false)">提交反馈</el-button>
          </template>
        </el-dialog>

        <!-- 预测历史 (最近 5 条) -->
        <div class="card history-card" v-if="recentHistory.length">
          <h3 class="card-title">最近预测</h3>
          <div
            v-for="item in recentHistory"
            :key="item.id"
            class="history-item"
          >
            <el-tag
              :type="item.prediction_label === 'spam' ? 'danger' : 'success'"
              size="small"
            >{{ item.prediction_label === 'spam' ? '垃圾' : '正常' }}</el-tag>
            <span class="history-text">{{ item.input_text }}</span>
            <span class="history-conf">{{ (item.confidence * 100).toFixed(0) }}%</span>
          </div>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { predictSingle, getPredictionHistory, submitFeedback } from '@/api/prediction'
import { ElMessage } from 'element-plus'
import { useUserStore } from '@/store/modules/user'
import {
  EditPen, Promotion, DataAnalysis, WarningFilled,
  CircleCheckFilled, ChatDotRound, Select, CloseBold,
} from '@element-plus/icons-vue'

const userStore = useUserStore()

const emailText = ref('')
const predicting = ref(false)
const result = ref(null)
const recentHistory = ref([])

// 反馈相关状态
const feedbackSubmitted = ref(false)
const feedbackLoading = ref(false)
const showWrongDialog = ref(false)
const wrongCorrectLabel = ref('ham')

const resultClass = computed(() => {
  if (!result.value) return ''
  return result.value.label === 'spam' ? 'result-spam' : 'result-ham'
})

const examples = {
  spam: '恭喜您！您已被选中为我们百万大奖抽奖活动的幸运获奖者！请立即点击下方链接领取您的奖金，此优惠限时有效，过期作废！同时需要您提供银行账户信息以完成身份核实，请尽快操作，切勿错过！',
  ham: '团队大家好，提醒一下明天上午10点我们照常举行每周项目同步会议。请大家提前查阅最新的迭代报告，并准备好各自的进度更新。如有需要补充的议题，请提前告知，谢谢。',
}

function fillExample(type) {
  emailText.value = examples[type]
}

async function handlePredict() {
  if (!emailText.value.trim()) return
  predicting.value = true
  result.value = null
  feedbackSubmitted.value = false
  try {
    const res = await predictSingle(emailText.value)
    result.value = res.data
    fetchRecentHistory()
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || '预测失败，请检查服务状态')
  } finally {
    predicting.value = false
  }
}

async function handleFeedback(isCorrect) {
  if (!result.value?.prediction_id) return
  feedbackLoading.value = true
  try {
    await submitFeedback({
      prediction_id: result.value.prediction_id,
      is_correct: isCorrect,
      correct_label: isCorrect ? null : wrongCorrectLabel.value,
    })
    feedbackSubmitted.value = true
    showWrongDialog.value = false
    ElMessage.success('感谢您的反馈！')
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || '反馈提交失败')
  } finally {
    feedbackLoading.value = false
  }
}

async function fetchRecentHistory() {
  try {
    const res = await getPredictionHistory({ page: 1, page_size: 5 })
    recentHistory.value = res.data
  } catch {
    // silent
  }
}

onMounted(() => {
  fetchRecentHistory()
})
</script>

<style scoped>
.predict-page {
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
  display: flex;
  align-items: center;
  gap: 6px;
}

/* Input */
.email-textarea :deep(.el-textarea__inner) {
  border-radius: 10px;
  font-size: 14px;
  line-height: 1.7;
  padding: 14px;
}
.input-actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 14px;
}
.char-count {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.4);
}
.predict-btn {
  border-radius: 10px;
  font-weight: 600;
  background: linear-gradient(135deg, #4f46e5, #7c3aed);
  border: none;
}
.predict-btn:hover:not(:disabled) {
  background: linear-gradient(135deg, #4338ca, #6d28d9);
}

/* Result card */
.result-card {
  transition: border-color 0.3s;
  border: 2px solid transparent;
}
.result-spam {
  border-color: #fecaca;
  background: linear-gradient(180deg, #fff5f5 0%, #fff 30%);
}
.result-ham {
  border-color: #bbf7d0;
  background: linear-gradient(180deg, #f0fdf4 0%, #fff 30%);
}

.result-main {
  text-align: center;
  padding: 20px 0;
}
.result-icon-wrapper {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 12px;
}
.icon-spam {
  background: #fef2f2;
  color: #ef4444;
}
.icon-ham {
  background: #f0fdf4;
  color: #10b981;
}
.result-label {
  font-size: 24px;
  font-weight: 700;
}
.label-spam { color: #ef4444; }
.label-ham { color: #10b981; }

/* Confidence */
.confidence-section {
  margin: 16px 0;
}
.confidence-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
  font-size: 14px;
  color: rgba(255, 255, 255, 0.55);
}
.confidence-value {
  font-weight: 700;
  color: #ffffff;
}

/* Details */
.result-details {
  background: rgba(255, 255, 255, 0.04);
  border-radius: 10px;
  padding: 14px 16px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.detail-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.detail-label {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.4);
}
.detail-value {
  font-size: 14px;
  font-weight: 500;
  color: rgba(255, 255, 255, 0.8);
}

/* Feedback */
.feedback-section {
  margin-top: 16px;
  padding-top: 14px;
  border-top: 1px solid rgba(255, 255, 255, 0.08);
  text-align: center;
}
.feedback-label {
  margin: 0 0 10px;
  font-size: 13px;
  color: rgba(255, 255, 255, 0.45);
}
.feedback-btns {
  display: flex;
  gap: 10px;
  justify-content: center;
}
.btn-correct {
  background: rgba(16, 185, 129, 0.12);
  border-color: rgba(16, 185, 129, 0.4);
  color: #10b981;
}
.btn-correct:hover {
  background: rgba(16, 185, 129, 0.22);
  border-color: #10b981;
}
.btn-wrong {
  background: rgba(239, 68, 68, 0.1);
  border-color: rgba(239, 68, 68, 0.4);
  color: #ef4444;
}
.btn-wrong:hover {
  background: rgba(239, 68, 68, 0.2);
  border-color: #ef4444;
}
.feedback-done {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  font-size: 13px;
  color: #10b981;
}

/* Empty state */
.result-empty {
  text-align: center;
  padding: 48px 0;
}
.result-empty p {
  color: rgba(255, 255, 255, 0.4);
  font-size: 14px;
  margin-top: 12px;
  line-height: 1.6;
}

/* History */
.history-card .card-title {
  font-size: 15px;
}
.history-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 0;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}
.history-item:last-child {
  border-bottom: none;
}
.history-text {
  flex: 1;
  font-size: 13px;
  color: rgba(255, 255, 255, 0.55);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.history-conf {
  font-size: 13px;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.8);
  flex-shrink: 0;
}
</style>
