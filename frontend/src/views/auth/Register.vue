<template>
  <div class="auth-page">
    <!-- Animated background shapes -->
    <div class="bg-shapes">
      <div class="shape shape-1"></div>
      <div class="shape shape-2"></div>
      <div class="shape shape-3"></div>
    </div>

    <!-- Main content -->
    <div class="auth-content">
      <!-- Left: Hero section -->
      <div class="hero-section">
        <div class="hero-text">
          <h1>加入我们<br /><span class="gradient-text">守护邮箱</span></h1>
          <p class="hero-desc">
            注册成为用户，即刻体验基于 BERT 深度学习的智能垃圾邮件识别服务。精准过滤、实时防护，让您的邮箱更安全。
          </p>
        </div>

        <!-- Feature highlights -->
        <div class="feature-list">
          <div class="feature-item">
            <div class="feature-icon icon-ai">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                <path d="M12 2a4 4 0 014 4v1a1 1 0 001 1h1a4 4 0 010 8h-1a1 1 0 00-1 1v1a4 4 0 01-8 0v-1a1 1 0 00-1-1H6a4 4 0 010-8h1a1 1 0 001-1V6a4 4 0 014-4z"/>
                <circle cx="12" cy="12" r="3"/>
              </svg>
            </div>
            <div>
              <h4>AI 智能检测</h4>
              <p>深度学习驱动的邮件内容分析</p>
            </div>
          </div>
          <div class="feature-item">
            <div class="feature-icon icon-shield">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
                <path d="M9 12l2 2 4-4"/>
              </svg>
            </div>
            <div>
              <h4>安全可靠</h4>
              <p>数据加密存储，隐私安全有保障</p>
            </div>
          </div>
          <div class="feature-item">
            <div class="feature-icon icon-speed">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>
              </svg>
            </div>
            <div>
              <h4>毫秒级响应</h4>
              <p>实时分析，即时返回分类结果</p>
            </div>
          </div>
        </div>
      </div>

      <!-- Right: Register form card -->
      <div class="form-section">
        <div class="form-card">
          <div class="form-header">
            <div class="logo-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                <path d="M16 21v-2a4 4 0 00-4-4H6a4 4 0 00-4 4v2"/>
                <circle cx="9" cy="7" r="4"/>
                <line x1="19" y1="8" x2="19" y2="14"/>
                <line x1="22" y1="11" x2="16" y2="11"/>
              </svg>
            </div>
            <h2>创建账户</h2>
            <p>填写以下信息完成注册</p>
          </div>

          <el-form :model="form" :rules="rules" ref="formRef" class="auth-form" @keyup.enter="handleRegister">
            <el-form-item prop="username">
              <el-input
                v-model="form.username"
                placeholder="请输入用户名"
                size="large"
                :prefix-icon="User"
              />
            </el-form-item>
            <el-form-item prop="email">
              <el-input
                v-model="form.email"
                placeholder="请输入邮箱"
                size="large"
                :prefix-icon="Message"
              />
            </el-form-item>
            <el-form-item prop="password">
              <el-input
                v-model="form.password"
                type="password"
                placeholder="请输入密码（不少于6位）"
                size="large"
                :prefix-icon="Lock"
                show-password
              />
            </el-form-item>
            <el-form-item>
              <el-button
                type="primary"
                :loading="loading"
                size="large"
                class="submit-btn"
                @click="handleRegister"
              >
                注 册
              </el-button>
            </el-form-item>
          </el-form>

          <div class="form-footer">
            <span>已有账号？</span>
            <router-link to="/login" class="link">去登录</router-link>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/store/modules/user'
import { ElMessage } from 'element-plus'
import { User, Lock, Message } from '@element-plus/icons-vue'

const router = useRouter()
const userStore = useUserStore()
const formRef = ref(null)
const loading = ref(false)

const form = reactive({ username: '', email: '', password: '' })
const rules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '请输入正确的邮箱地址', trigger: 'blur' },
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码不少于6位', trigger: 'blur' },
  ],
}

async function handleRegister() {
  await formRef.value.validate()
  loading.value = true
  try {
    await userStore.registerAction(form)
    ElMessage.success('注册成功，请登录')
    router.push('/login')
  } catch (err) {
    const msg = err.response?.data?.detail || '注册失败，请稍后再试'
    ElMessage.error(msg)
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
/* ===== Page Layout ===== */
.auth-page {
  min-height: 100vh;
  background: #0b0f1a;
  position: relative;
  overflow: hidden;
}

/* ===== Animated Background ===== */
.bg-shapes .shape {
  position: absolute;
  border-radius: 50%;
  filter: blur(80px);
  opacity: 0.5;
}
.shape-1 {
  width: 600px; height: 600px;
  background: radial-gradient(circle, #7c3aed 0%, transparent 70%);
  top: -200px; right: -100px;
  animation: float1 20s ease-in-out infinite;
}
.shape-2 {
  width: 500px; height: 500px;
  background: radial-gradient(circle, #4f46e5 0%, transparent 70%);
  bottom: -150px; left: -100px;
  animation: float2 25s ease-in-out infinite;
}
.shape-3 {
  width: 300px; height: 300px;
  background: radial-gradient(circle, #06b6d4 0%, transparent 70%);
  top: 50%; left: 50%;
  transform: translate(-50%, -50%);
  animation: float3 15s ease-in-out infinite;
}

@keyframes float1 {
  0%, 100% { transform: translate(0, 0); }
  50% { transform: translate(-60px, 40px); }
}
@keyframes float2 {
  0%, 100% { transform: translate(0, 0); }
  50% { transform: translate(40px, -60px); }
}
@keyframes float3 {
  0%, 100% { transform: translate(-50%, -50%) scale(1); }
  50% { transform: translate(-50%, -50%) scale(1.2); }
}

/* ===== Content Grid ===== */
.auth-content {
  position: relative;
  z-index: 1;
  display: flex;
  min-height: 100vh;
  max-width: 1400px;
  margin: 0 auto;
  padding: 40px;
  gap: 60px;
  align-items: center;
}

/* ===== Hero Section ===== */
.hero-section {
  flex: 1;
}
.hero-text h1 {
  font-size: 52px;
  font-weight: 800;
  color: #ffffff;
  line-height: 1.15;
  margin: 0 0 24px;
  letter-spacing: -1px;
}
.gradient-text {
  background: linear-gradient(135deg, #818cf8, #c084fc, #22d3ee);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}
.hero-desc {
  font-size: 17px;
  color: rgba(255, 255, 255, 0.6);
  line-height: 1.7;
  max-width: 480px;
  margin-bottom: 48px;
}

/* ===== Feature List ===== */
.feature-list {
  display: flex;
  flex-direction: column;
  gap: 24px;
}
.feature-item {
  display: flex;
  align-items: center;
  gap: 16px;
}
.feature-icon {
  width: 44px; height: 44px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.feature-icon svg {
  width: 22px; height: 22px;
}
.icon-ai {
  background: rgba(129, 140, 248, 0.15);
  color: #818cf8;
}
.icon-shield {
  background: rgba(52, 211, 153, 0.15);
  color: #34d399;
}
.icon-speed {
  background: rgba(251, 191, 36, 0.15);
  color: #fbbf24;
}
.feature-item h4 {
  margin: 0 0 2px;
  font-size: 15px;
  font-weight: 600;
  color: #ffffff;
}
.feature-item p {
  margin: 0;
  font-size: 13px;
  color: rgba(255, 255, 255, 0.45);
}

/* ===== Form Section ===== */
.form-section {
  width: 440px;
  flex-shrink: 0;
}
.form-card {
  background: rgba(255, 255, 255, 0.06);
  backdrop-filter: blur(40px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 24px;
  padding: 44px 40px;
}

.form-header {
  text-align: center;
  margin-bottom: 32px;
}
.logo-icon {
  width: 52px; height: 52px;
  margin: 0 auto 20px;
  background: linear-gradient(135deg, #7c3aed, #4f46e5);
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
}
.logo-icon svg {
  width: 28px; height: 28px;
  color: #ffffff;
}
.form-header h2 {
  font-size: 26px;
  font-weight: 700;
  color: #ffffff;
  margin: 0 0 8px;
}
.form-header p {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.45);
  margin: 0;
}

/* ===== Form Overrides ===== */
.auth-form :deep(.el-input__wrapper) {
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  box-shadow: none;
  padding: 4px 16px;
  transition: all 0.3s;
}
.auth-form :deep(.el-input__wrapper:hover),
.auth-form :deep(.el-input__wrapper.is-focus) {
  border-color: rgba(129, 140, 248, 0.5);
  background: rgba(255, 255, 255, 0.08);
  box-shadow: 0 0 0 3px rgba(79, 70, 229, 0.15);
}
.auth-form :deep(.el-input__inner) {
  color: #ffffff;
  font-size: 15px;
}
.auth-form :deep(.el-input__inner::placeholder) {
  color: rgba(255, 255, 255, 0.35);
}
.auth-form :deep(.el-input__prefix .el-icon) {
  color: rgba(255, 255, 255, 0.4);
  font-size: 18px;
}
.auth-form :deep(.el-input__suffix .el-icon) {
  color: rgba(255, 255, 255, 0.4);
}
.auth-form :deep(.el-form-item__error) {
  padding-top: 4px;
}

.submit-btn {
  width: 100%;
  height: 48px;
  border-radius: 12px;
  font-size: 16px;
  font-weight: 600;
  letter-spacing: 4px;
  border: none;
  background: linear-gradient(135deg, #7c3aed, #4f46e5);
  transition: all 0.3s;
}
.submit-btn:hover {
  background: linear-gradient(135deg, #6d28d9, #4338ca);
  transform: translateY(-1px);
  box-shadow: 0 8px 25px rgba(124, 58, 237, 0.4);
}

/* ===== Footer Link ===== */
.form-footer {
  text-align: center;
  margin-top: 24px;
  font-size: 14px;
  color: rgba(255, 255, 255, 0.45);
}
.form-footer .link {
  color: #818cf8;
  text-decoration: none;
  font-weight: 500;
  margin-left: 4px;
  transition: color 0.2s;
}
.form-footer .link:hover {
  color: #a5b4fc;
}

/* ===== Responsive ===== */
@media (max-width: 1024px) {
  .auth-content {
    flex-direction: column;
    justify-content: center;
    padding: 40px 24px;
    gap: 40px;
  }
  .hero-section {
    text-align: center;
  }
  .hero-text h1 {
    font-size: 36px;
  }
  .hero-desc {
    margin: 0 auto 36px;
  }
  .feature-list {
    align-items: center;
  }
  .form-section {
    width: 100%;
    max-width: 440px;
  }
  .form-card {
    padding: 36px 28px;
  }
}
</style>
