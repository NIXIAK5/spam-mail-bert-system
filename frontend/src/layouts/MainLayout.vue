<template>
  <el-container :class="['main-layout', themeStore.isDark ? 'dark-app' : 'light-app']">
    <el-aside :width="isCollapse ? '64px' : '240px'" class="aside">
      <div class="logo">
        <div class="logo-icon">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
            <rect x="2" y="4" width="20" height="16" rx="3"/>
            <path d="M22 4L12 13 2 4"/>
          </svg>
        </div>
        <span v-if="!isCollapse" class="logo-text">邮件分类系统</span>
      </div>
      <el-menu
        :default-active="$route.path"
        :collapse="isCollapse"
        router
        background-color="transparent"
        text-color="rgba(255,255,255,0.55)"
        active-text-color="#a5b4fc"
        class="dark-menu"
      >
        <!-- ========== 管理员菜单 ========== -->
        <template v-if="userStore.isAdmin">
          <el-menu-item index="/dashboard">
            <el-icon><DataBoard /></el-icon>
            <template #title>管理控制台</template>
          </el-menu-item>

          <div v-if="!isCollapse" class="menu-group-label">预测功能</div>
          <el-menu-item index="/predict">
            <el-icon><ChatDotRound /></el-icon>
            <template #title>模型预测</template>
          </el-menu-item>
          <el-menu-item index="/predict/batch">
            <el-icon><Files /></el-icon>
            <template #title>批量预测</template>
          </el-menu-item>
          <el-menu-item index="/history">
            <el-icon><Clock /></el-icon>
            <template #title>预测记录</template>
          </el-menu-item>
          <el-menu-item index="/analysis">
            <el-icon><TrendCharts /></el-icon>
            <template #title>数据分析</template>
          </el-menu-item>

          <div v-if="!isCollapse" class="menu-group-label">模型管理</div>
          <el-menu-item index="/model">
            <el-icon><Cpu /></el-icon>
            <template #title>模型评估</template>
          </el-menu-item>
          <el-menu-item index="/admin/training">
            <el-icon><Operation /></el-icon>
            <template #title>模型训练</template>
          </el-menu-item>

          <el-menu-item index="/admin/export">
            <el-icon><Download /></el-icon>
            <template #title>模型导出</template>
          </el-menu-item>

          <div v-if="!isCollapse" class="menu-group-label">系统管理</div>
          <el-menu-item index="/admin/users">
            <el-icon><User /></el-icon>
            <template #title>用户管理</template>
          </el-menu-item>
          <el-menu-item index="/admin/feedback">
            <el-icon><ChatLineSquare /></el-icon>
            <template #title>反馈管理</template>
          </el-menu-item>
          <el-menu-item index="/dataset">
            <el-icon><Folder /></el-icon>
            <template #title>数据集管理</template>
          </el-menu-item>
          <el-menu-item index="/admin/datasets">
            <el-icon><FolderOpened /></el-icon>
            <template #title>数据集维护</template>
          </el-menu-item>
        </template>

        <!-- ========== 普通用户菜单 ========== -->
        <template v-else>
          <el-menu-item index="/dashboard">
            <el-icon><HomeFilled /></el-icon>
            <template #title>我的首页</template>
          </el-menu-item>
          <el-menu-item index="/predict">
            <el-icon><ChatDotRound /></el-icon>
            <template #title>邮件检测</template>
          </el-menu-item>
          <el-menu-item index="/predict/batch">
            <el-icon><Files /></el-icon>
            <template #title>批量检测</template>
          </el-menu-item>
          <el-menu-item index="/history">
            <el-icon><Clock /></el-icon>
            <template #title>我的记录</template>
          </el-menu-item>
          <el-menu-item index="/analysis">
            <el-icon><TrendCharts /></el-icon>
            <template #title>结果分析</template>
          </el-menu-item>
          <el-menu-item index="/dataset">
            <el-icon><Folder /></el-icon>
            <template #title>数据浏览</template>
          </el-menu-item>
          <el-menu-item index="/model">
            <el-icon><Cpu /></el-icon>
            <template #title>模型概览</template>
          </el-menu-item>
        </template>
      </el-menu>
    </el-aside>

    <el-container>
      <el-header class="header">
        <div class="header-left">
          <el-icon class="collapse-btn" @click="isCollapse = !isCollapse">
            <Fold v-if="!isCollapse" />
            <Expand v-else />
          </el-icon>
          <el-breadcrumb separator="/">
            <el-breadcrumb-item>{{ dynamicTitle }}</el-breadcrumb-item>
          </el-breadcrumb>
        </div>
        <div class="header-right">
          <el-tooltip :content="themeStore.isDark ? '切换到浅色模式' : '切换到深色模式'" placement="bottom">
            <el-icon class="theme-toggle" @click="themeStore.toggle">
              <Sunny v-if="themeStore.isDark" />
              <Moon v-else />
            </el-icon>
          </el-tooltip>
          <el-dropdown>
            <span class="user-info">
              <el-avatar :size="30" class="user-avatar">
                {{ userStore.username?.charAt(0)?.toUpperCase() }}
              </el-avatar>
              {{ userStore.username }}
              <el-icon><ArrowDown /></el-icon>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item @click="$router.push('/profile')">个人信息</el-dropdown-item>
                <el-dropdown-item divided @click="handleLogout">退出登录</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>

      <el-main class="main-content">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useUserStore } from '@/store/modules/user'
import { useThemeStore } from '@/store/modules/theme'
import {
  DataBoard, Folder, FolderOpened, ChatDotRound, Files, Clock,
  TrendCharts, Cpu, Fold, Expand, ArrowDown,
  Sunny, Moon, HomeFilled, Operation, Download, User, ChatLineSquare,
} from '@element-plus/icons-vue'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()
const themeStore = useThemeStore()
const isCollapse = ref(false)

const userTitleMap = {
  '/dashboard': '我的首页',
  '/predict': '邮件检测',
  '/predict/batch': '批量检测',
  '/history': '我的记录',
  '/analysis': '结果分析',
  '/dataset': '数据浏览',
  '/model': '模型概览',
}

const adminTitleMap = {
  '/dashboard': '管理控制台',
  '/analysis': '数据分析',
  '/admin/feedback': '反馈管理',
}

const dynamicTitle = computed(() => {
  const path = route.path
  if (userStore.isAdmin) {
    return adminTitleMap[path] || route.meta.title || '首页'
  }
  return userTitleMap[path] || route.meta.title || '首页'
})

onMounted(async () => {
  if (userStore.isLoggedIn && !userStore.userInfo) {
    await userStore.fetchUserInfo()
  }
})

function handleLogout() {
  userStore.logout()
  router.push('/login')
}
</script>

<style scoped>
.main-layout {
  height: 100vh;
  transition: background 0.3s;
}
.dark-app.main-layout { background: #0b0f1a; }
.light-app.main-layout { background: #f0f2f5; }

/* ===== Sidebar (dark in both themes) ===== */
.aside {
  transition: width 0.3s, background 0.3s;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}
.dark-app .aside {
  background: rgba(255, 255, 255, 0.03);
  border-right: 1px solid rgba(255, 255, 255, 0.06);
}
.light-app .aside {
  background: #1e293b;
  border-right: none;
  box-shadow: 2px 0 8px rgba(0, 0, 0, 0.08);
}

.logo {
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 0 16px;
  flex-shrink: 0;
}
.dark-app .logo { border-bottom: 1px solid rgba(255, 255, 255, 0.06); }
.light-app .logo { border-bottom: 1px solid rgba(255, 255, 255, 0.08); }

.logo-icon {
  width: 34px;
  height: 34px;
  background: linear-gradient(135deg, #4f46e5, #7c3aed);
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.logo-icon svg {
  width: 18px;
  height: 18px;
  color: #fff;
}
.logo-text {
  color: #fff;
  font-size: 15px;
  font-weight: 700;
  white-space: nowrap;
  letter-spacing: 0.5px;
}

/* Menu styles */
.dark-menu {
  border-right: none;
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}
.menu-group-label {
  padding: 16px 12px 6px;
  font-size: 11px;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.25);
  letter-spacing: 1px;
  text-transform: uppercase;
}
.dark-menu :deep(.el-menu-item),
.dark-menu :deep(.el-sub-menu__title) {
  border-radius: 8px;
  margin-bottom: 2px;
  height: 44px;
  line-height: 44px;
}
.dark-menu :deep(.el-menu-item:hover),
.dark-menu :deep(.el-sub-menu__title:hover) {
  background-color: rgba(255, 255, 255, 0.06);
}
.dark-menu :deep(.el-menu-item.is-active) {
  background: rgba(99, 102, 241, 0.15);
  color: #a5b4fc;
}
.dark-menu :deep(.el-sub-menu .el-menu) {
  background-color: transparent;
}
.dark-menu :deep(.el-sub-menu .el-menu-item) {
  padding-left: 48px !important;
  height: 40px;
  line-height: 40px;
  font-size: 13px;
}
.dark-menu :deep(.el-menu-item .el-icon),
.dark-menu :deep(.el-sub-menu__title .el-icon) {
  color: inherit;
}
.dark-menu :deep(.el-sub-menu__icon-arrow) {
  color: rgba(255, 255, 255, 0.35);
}

/* ===== Header ===== */
.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 60px;
  padding: 0 24px;
  transition: background 0.3s, border-color 0.3s;
}
.dark-app .header {
  background: rgba(255, 255, 255, 0.03);
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}
.light-app .header {
  background: #fff;
  border-bottom: 1px solid #f3f4f6;
  box-shadow: 0 1px 4px rgba(0, 21, 41, 0.04);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}
.collapse-btn {
  font-size: 20px;
  cursor: pointer;
  transition: color 0.2s;
}
.dark-app .collapse-btn { color: rgba(255, 255, 255, 0.55); }
.light-app .collapse-btn { color: #6b7280; }
.collapse-btn:hover { color: #a5b4fc; }

.header-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

/* Theme toggle */
.theme-toggle {
  font-size: 20px;
  cursor: pointer;
  transition: color 0.2s, transform 0.3s;
}
.dark-app .theme-toggle { color: rgba(255, 255, 255, 0.55); }
.light-app .theme-toggle { color: #6b7280; }
.theme-toggle:hover {
  color: #a5b4fc;
  transform: rotate(30deg);
}

.user-info {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  font-size: 14px;
  transition: color 0.2s;
}
.dark-app .user-info { color: rgba(255, 255, 255, 0.75); }
.light-app .user-info { color: #374151; }
.user-info:hover { color: #a5b4fc; }

.user-avatar {
  background: linear-gradient(135deg, #4f46e5, #7c3aed);
  color: #fff;
  font-size: 13px;
  font-weight: 600;
  border: none;
}

/* ===== Main Content ===== */
.main-content {
  min-height: 0;
  overflow-y: auto;
  padding: 24px;
  position: relative;
}

/* 背景图层：深色和浅色模式都显示 */
.main-content::before {
  content: '';
  position: fixed;
  inset: 0;
  background: url('@/assets/images/letters-5614727_640.webp') center / cover no-repeat;
  pointer-events: none;
  z-index: 0;
  transition: opacity 0.3s;
}
.dark-app .main-content::before {
  opacity: 0.2;
}
.light-app .main-content::before {
  opacity: 0.05;
}

/* 遮罩层：纯色，只过渡 background-color */
.dark-app .main-content {
  background: rgba(11, 15, 26, 0.82);
  transition: background 0.3s;
}
.light-app .main-content {
  background: rgba(240, 242, 245, 0.88);
  transition: background 0.3s;
}

/* 内容层浮于背景之上 */
.main-content > * {
  position: relative;
  z-index: 1;
}
</style>
