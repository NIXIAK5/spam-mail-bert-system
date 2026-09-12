<template>
  <div class="profile-page">
    <div class="profile-header-card">
      <div class="profile-banner"></div>
      <div class="profile-avatar-row">
        <div class="avatar-wrapper">
          <el-avatar :size="88" :src="avatarUrl">
            {{ userStore.username?.charAt(0)?.toUpperCase() }}
          </el-avatar>
          <div class="avatar-badge" :class="userStore.isAdmin ? 'badge-admin' : 'badge-normal'">
            {{ userStore.isAdmin ? '管理员' : '普通用户' }}
          </div>
        </div>
        <div class="profile-summary">
          <h2>{{ userStore.userInfo?.username }}</h2>
          <p>{{ userStore.userInfo?.email }}</p>
          <p class="join-date">
            <el-icon><Calendar /></el-icon>
            注册于 {{ formatDate(userStore.userInfo?.created_at) }}
          </p>
        </div>
      </div>
    </div>

    <div class="profile-body">
      <el-tabs v-model="activeTab" class="profile-tabs">
        <!-- Personal info tab -->
        <el-tab-pane label="个人信息" name="info">
          <div class="tab-content">
            <div class="section-header">
              <h3>基本信息</h3>
              <p>查看和修改您的个人资料</p>
            </div>
            <el-form
              ref="profileFormRef"
              :model="profileForm"
              :rules="profileRules"
              label-position="top"
              class="profile-form"
            >
              <el-row :gutter="24">
                <el-col :span="12">
                  <el-form-item label="用户名" prop="username">
                    <el-input
                      v-model="profileForm.username"
                      placeholder="请输入用户名"
                      :prefix-icon="User"
                      size="large"
                    />
                  </el-form-item>
                </el-col>
                <el-col :span="12">
                  <el-form-item label="邮箱" prop="email">
                    <el-input
                      v-model="profileForm.email"
                      placeholder="请输入邮箱"
                      :prefix-icon="Message"
                      size="large"
                    />
                  </el-form-item>
                </el-col>
              </el-row>
              <el-row :gutter="24">
                <el-col :span="12">
                  <el-form-item label="角色">
                    <el-input
                      :model-value="userStore.isAdmin ? '管理员' : '普通用户'"
                      disabled
                      size="large"
                      :prefix-icon="UserFilled"
                    />
                  </el-form-item>
                </el-col>
                <el-col :span="12">
                  <el-form-item label="账户状态">
                    <el-input
                      :model-value="userStore.userInfo?.is_active ? '正常' : '已禁用'"
                      disabled
                      size="large"
                    />
                  </el-form-item>
                </el-col>
              </el-row>
              <el-form-item>
                <el-button
                  type="primary"
                  size="large"
                  :loading="profileLoading"
                  @click="handleUpdateProfile"
                  class="save-btn"
                >
                  <el-icon><Check /></el-icon>
                  保存修改
                </el-button>
              </el-form-item>
            </el-form>
          </div>
        </el-tab-pane>

        <!-- Password change tab -->
        <el-tab-pane label="修改密码" name="password">
          <div class="tab-content">
            <div class="section-header">
              <h3>修改密码</h3>
              <p>定期更换密码以保障您的账户安全</p>
            </div>
            <el-form
              ref="passwordFormRef"
              :model="passwordForm"
              :rules="passwordRules"
              label-position="top"
              class="profile-form password-form"
            >
              <el-form-item label="当前密码" prop="old_password">
                <el-input
                  v-model="passwordForm.old_password"
                  type="password"
                  placeholder="请输入当前密码"
                  :prefix-icon="Lock"
                  show-password
                  size="large"
                />
              </el-form-item>
              <el-form-item label="新密码" prop="new_password">
                <el-input
                  v-model="passwordForm.new_password"
                  type="password"
                  placeholder="请输入新密码（不少于6位）"
                  :prefix-icon="Lock"
                  show-password
                  size="large"
                />
              </el-form-item>
              <el-form-item label="确认新密码" prop="confirm_password">
                <el-input
                  v-model="passwordForm.confirm_password"
                  type="password"
                  placeholder="请再次输入新密码"
                  :prefix-icon="Lock"
                  show-password
                  size="large"
                />
              </el-form-item>
              <el-form-item>
                <el-button
                  type="primary"
                  size="large"
                  :loading="passwordLoading"
                  @click="handleChangePassword"
                  class="save-btn"
                >
                  <el-icon><Check /></el-icon>
                  确认修改
                </el-button>
              </el-form-item>
            </el-form>
          </div>
        </el-tab-pane>
      </el-tabs>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { useUserStore } from '@/store/modules/user'
import { updateProfile, changePassword } from '@/api/user'
import { ElMessage } from 'element-plus'
import { User, Lock, Message, UserFilled, Check, Calendar } from '@element-plus/icons-vue'

const userStore = useUserStore()
const activeTab = ref('info')

const profileFormRef = ref(null)
const passwordFormRef = ref(null)
const profileLoading = ref(false)
const passwordLoading = ref(false)

const avatarUrl = computed(() => userStore.userInfo?.avatar || '')

const profileForm = reactive({
  username: '',
  email: '',
})

const passwordForm = reactive({
  old_password: '',
  new_password: '',
  confirm_password: '',
})

const profileRules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '请输入正确的邮箱地址', trigger: 'blur' },
  ],
}

const validateConfirmPassword = (rule, value, callback) => {
  if (value !== passwordForm.new_password) {
    callback(new Error('两次输入的密码不一致'))
  } else {
    callback()
  }
}

const passwordRules = {
  old_password: [{ required: true, message: '请输入当前密码', trigger: 'blur' }],
  new_password: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, message: '密码不少于6位', trigger: 'blur' },
  ],
  confirm_password: [
    { required: true, message: '请再次输入新密码', trigger: 'blur' },
    { validator: validateConfirmPassword, trigger: 'blur' },
  ],
}

function formatDate(dateStr) {
  if (!dateStr) return '--'
  const d = new Date(dateStr)
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}

function loadUserInfo() {
  if (userStore.userInfo) {
    profileForm.username = userStore.userInfo.username || ''
    profileForm.email = userStore.userInfo.email || ''
  }
}

async function handleUpdateProfile() {
  await profileFormRef.value.validate()
  profileLoading.value = true
  try {
    await updateProfile({
      username: profileForm.username,
      email: profileForm.email,
    })
    await userStore.fetchUserInfo()
    loadUserInfo()
    ElMessage.success('个人信息更新成功')
  } catch (err) {
    const msg = err.response?.data?.detail || '更新失败，请稍后再试'
    ElMessage.error(msg)
  } finally {
    profileLoading.value = false
  }
}

async function handleChangePassword() {
  await passwordFormRef.value.validate()
  passwordLoading.value = true
  try {
    await changePassword({
      old_password: passwordForm.old_password,
      new_password: passwordForm.new_password,
    })
    ElMessage.success('密码修改成功')
    passwordForm.old_password = ''
    passwordForm.new_password = ''
    passwordForm.confirm_password = ''
  } catch (err) {
    const msg = err.response?.data?.detail || '密码修改失败'
    ElMessage.error(msg)
  } finally {
    passwordLoading.value = false
  }
}

onMounted(() => {
  loadUserInfo()
})
</script>

<style scoped>
.profile-page {
  max-width: 960px;
  margin: 0 auto;
}

/* ===== Header Card with Banner ===== */
.profile-header-card {
  background: rgba(255, 255, 255, 0.06);
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
  border: 1px solid rgba(255, 255, 255, 0.08);
  backdrop-filter: blur(20px);
  margin-bottom: 20px;
}
.profile-banner {
  height: 120px;
  background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 50%, #a855f7 100%);
}
.profile-avatar-row {
  display: flex;
  align-items: flex-end;
  gap: 24px;
  padding: 0 32px 24px;
  margin-top: -44px;
}
.avatar-wrapper {
  position: relative;
  flex-shrink: 0;
}
.avatar-wrapper .el-avatar {
  border: 4px solid rgba(255, 255, 255, 0.1);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  background: linear-gradient(135deg, #4f46e5, #7c3aed);
  color: #fff;
  font-size: 32px;
  font-weight: 700;
}
.avatar-badge {
  position: absolute;
  bottom: -4px;
  left: 50%;
  transform: translateX(-50%);
  padding: 2px 10px;
  border-radius: 10px;
  font-size: 11px;
  font-weight: 600;
  white-space: nowrap;
  color: #fff;
}
.badge-admin {
  background: linear-gradient(135deg, #f59e0b, #ef4444);
}
.badge-normal {
  background: linear-gradient(135deg, #3b82f6, #6366f1);
}
.profile-summary {
  padding-bottom: 4px;
}
.profile-summary h2 {
  margin: 0 0 4px;
  font-size: 22px;
  font-weight: 700;
  color: #ffffff;
}
.profile-summary p {
  margin: 0;
  font-size: 14px;
  color: rgba(255, 255, 255, 0.55);
}
.join-date {
  display: flex;
  align-items: center;
  gap: 4px;
  margin-top: 4px !important;
  font-size: 13px !important;
  color: rgba(255, 255, 255, 0.4) !important;
}

/* ===== Tabs Body ===== */
.profile-body {
  background: rgba(255, 255, 255, 0.06);
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
  border: 1px solid rgba(255, 255, 255, 0.08);
  backdrop-filter: blur(20px);
  padding: 8px 32px 32px;
}
.profile-tabs :deep(.el-tabs__header) {
  margin-bottom: 0;
}
.profile-tabs :deep(.el-tabs__nav-wrap::after) {
  height: 1px;
  background: rgba(255, 255, 255, 0.06);
}
.profile-tabs :deep(.el-tabs__item) {
  font-size: 15px;
  font-weight: 500;
  padding: 0 20px;
  height: 48px;
  line-height: 48px;
}
.profile-tabs :deep(.el-tabs__active-bar) {
  background: linear-gradient(90deg, #4f46e5, #7c3aed);
  height: 3px;
  border-radius: 2px;
}

.tab-content {
  padding-top: 28px;
}
.section-header {
  margin-bottom: 28px;
}
.section-header h3 {
  margin: 0 0 6px;
  font-size: 18px;
  font-weight: 700;
  color: #ffffff;
}
.section-header p {
  margin: 0;
  font-size: 14px;
  color: rgba(255, 255, 255, 0.4);
}

/* ===== Form Styling ===== */
.profile-form :deep(.el-form-item__label) {
  font-weight: 600;
  color: rgba(255, 255, 255, 0.65);
  font-size: 14px;
}
.profile-form :deep(.el-input__wrapper) {
  border-radius: 10px;
  box-shadow: 0 0 0 1px rgba(255, 255, 255, 0.1);
  transition: all 0.2s;
}
.profile-form :deep(.el-input__wrapper:hover) {
  box-shadow: 0 0 0 1px rgba(129, 140, 248, 0.4);
}
.profile-form :deep(.el-input__wrapper.is-focus) {
  box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.3);
}
.profile-form :deep(.el-input.is-disabled .el-input__wrapper) {
  background: rgba(255, 255, 255, 0.03);
}

.password-form {
  max-width: 480px;
}

.save-btn {
  margin-top: 8px;
  padding: 0 32px;
  border-radius: 10px;
  font-weight: 600;
  background: linear-gradient(135deg, #4f46e5, #7c3aed);
  border: none;
  transition: all 0.3s;
}
.save-btn:hover {
  background: linear-gradient(135deg, #4338ca, #6d28d9);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(79, 70, 229, 0.35);
}
</style>
