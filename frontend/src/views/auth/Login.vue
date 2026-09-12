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
          <h1>智能识别<br /><span class="gradient-text">垃圾邮件</span></h1>
          <p class="hero-desc">
            基于 BERT 深度学习模型，为您的邮箱提供精准的垃圾邮件分类识别服务，让每一封重要邮件都不被错过。
          </p>
          <div class="hero-stats">
            <div class="stat-item">
              <span class="stat-number">99.2%</span>
              <span class="stat-label">识别准确率</span>
            </div>
            <div class="stat-item">
              <span class="stat-number">BERT</span>
              <span class="stat-label">深度学习模型</span>
            </div>
            <div class="stat-item">
              <span class="stat-number">&lt;1s</span>
              <span class="stat-label">实时响应</span>
            </div>
          </div>
        </div>

        <!-- Floating image card -->
        <div class="floating-cards">
          <div class="float-card card-1">
            <img src="@/assets/images/letter-8052497_640.png" alt="mail" />
          </div>
        </div>
      </div>

      <!-- Right: Login form card -->
      <div class="form-section">
        <div class="form-card">
          <div class="form-header">
            <div class="logo-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                <rect x="2" y="4" width="20" height="16" rx="3"/>
                <path d="M22 4L12 13 2 4"/>
              </svg>
            </div>
            <h2>欢迎回来</h2>
            <p>登录您的账户以继续使用系统</p>
          </div>

          <el-form :model="form" :rules="rules" ref="formRef" class="auth-form" @keyup.enter="handleLogin">
            <el-form-item prop="username">
              <el-input
                v-model="form.username"
                placeholder="请输入用户名"
                size="large"
                :prefix-icon="User"
              />
            </el-form-item>
            <el-form-item prop="password">
              <el-input
                v-model="form.password"
                type="password"
                placeholder="请输入密码"
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
                @click="handleLogin"
              >
                登 录
              </el-button>
            </el-form-item>
          </el-form>

          <div class="form-footer">
            <span>还没有账号？</span>
            <router-link to="/register" class="link">立即注册</router-link>
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
import { User, Lock } from '@element-plus/icons-vue'

const router = useRouter()
const userStore = useUserStore()
const formRef = ref(null)
const loading = ref(false)

const form = reactive({ username: '', password: '' })
const rules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
}

async function handleLogin() {
  await formRef.value.validate()
  loading.value = true
  try {
    await userStore.loginAction(form.username, form.password)
    ElMessage.success('登录成功')
    router.push('/')
  } catch (err) {
    const msg = err.response?.data?.detail || '登录失败，请检查用户名和密码'
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
  background: radial-gradient(circle, #4f46e5 0%, transparent 70%);
  top: -200px; left: -100px;
  animation: float1 20s ease-in-out infinite;
}
.shape-2 {
  width: 500px; height: 500px;
  background: radial-gradient(circle, #7c3aed 0%, transparent 70%);
  bottom: -150px; right: -100px;
  animation: float2 25s ease-in-out infinite;
}
.shape-3 {
  width: 300px; height: 300px;
  background: radial-gradient(circle, #2563eb 0%, transparent 70%);
  top: 50%; left: 50%;
  transform: translate(-50%, -50%);
  animation: float3 15s ease-in-out infinite;
}

@keyframes float1 {
  0%, 100% { transform: translate(0, 0); }
  50% { transform: translate(60px, 40px); }
}
@keyframes float2 {
  0%, 100% { transform: translate(0, 0); }
  50% { transform: translate(-40px, -60px); }
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
  position: relative;
}
.hero-text h1 {
  font-size: 56px;
  font-weight: 800;
  color: #ffffff;
  line-height: 1.15;
  margin: 0 0 24px;
  letter-spacing: -1px;
}
.gradient-text {
  background: linear-gradient(135deg, #818cf8, #c084fc, #f472b6);
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

/* Stats row */
.hero-stats {
  display: flex;
  gap: 40px;
}
.stat-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.stat-number {
  font-size: 28px;
  font-weight: 700;
  color: #ffffff;
}
.stat-label {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.45);
}

/* ===== Floating Image Cards ===== */
.floating-cards {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
}
.float-card {
  position: absolute;
  border-radius: 16px;
  overflow: hidden;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.4);
  animation: cardFloat 6s ease-in-out infinite;
}
.float-card img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.card-1 {
  width: 180px; height: 180px;
  top: -10px; right: 20px;
  border: 2px solid rgba(255, 255, 255, 0.1);
  background: rgba(255, 255, 255, 0.05);
}

@keyframes cardFloat {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-12px); }
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
  padding: 48px 40px;
}

.form-header {
  text-align: center;
  margin-bottom: 36px;
}
.logo-icon {
  width: 52px; height: 52px;
  margin: 0 auto 20px;
  background: linear-gradient(135deg, #4f46e5, #7c3aed);
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
  background: linear-gradient(135deg, #4f46e5, #7c3aed);
  transition: all 0.3s;
}
.submit-btn:hover {
  background: linear-gradient(135deg, #4338ca, #6d28d9);
  transform: translateY(-1px);
  box-shadow: 0 8px 25px rgba(79, 70, 229, 0.4);
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
    font-size: 38px;
  }
  .hero-desc {
    margin: 0 auto 36px;
  }
  .hero-stats {
    justify-content: center;
  }
  .floating-cards {
    display: none;
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
