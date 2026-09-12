import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/auth/Login.vue'),
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('@/views/auth/Register.vue'),
  },
  {
    path: '/',
    component: () => import('@/layouts/MainLayout.vue'),
    redirect: '/dashboard',
    meta: { requiresAuth: true },
    children: [
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('@/views/dashboard/Index.vue'),
        meta: { title: '系统首页' },
      },
      {
        path: 'profile',
        name: 'Profile',
        component: () => import('@/views/profile/Index.vue'),
        meta: { title: '个人信息' },
      },
      {
        path: 'dataset',
        name: 'Dataset',
        component: () => import('@/views/dataset/Index.vue'),
        meta: { title: '数据集管理' },
      },
      {
        path: 'dataset/:id/preview',
        name: 'DatasetPreview',
        component: () => import('@/views/dataset/Preview.vue'),
        meta: { title: '数据集预览' },
      },
      {
        path: 'predict',
        name: 'Predict',
        component: () => import('@/views/predict/Index.vue'),
        meta: { title: '模型预测' },
      },
      {
        path: 'predict/batch',
        name: 'BatchPredict',
        component: () => import('@/views/predict/Batch.vue'),
        meta: { title: '批量预测' },
      },
      {
        path: 'history',
        name: 'History',
        component: () => import('@/views/history/Index.vue'),
        meta: { title: '预测记录' },
      },
      {
        path: 'analysis',
        name: 'Analysis',
        component: () => import('@/views/analysis/Index.vue'),
        meta: { title: '预测结果展示' },
      },
      {
        path: 'model',
        name: 'ModelList',
        component: () => import('@/views/model/Index.vue'),
        meta: { title: '模型评估' },
      },
      {
        path: 'model/:id',
        name: 'ModelDetail',
        component: () => import('@/views/model/Detail.vue'),
        meta: { title: '模型详情' },
      },
      // 管理员路由
      {
        path: 'admin/users',
        name: 'AdminUsers',
        component: () => import('@/views/admin/Users.vue'),
        meta: { title: '用户管理', requiresAdmin: true },
      },
      {
        path: 'admin/datasets',
        name: 'AdminDatasets',
        component: () => import('@/views/admin/Datasets.vue'),
        meta: { title: '数据集维护', requiresAdmin: true },
      },
      {
        path: 'admin/training',
        name: 'AdminTraining',
        component: () => import('@/views/admin/Training.vue'),
        meta: { title: '模型训练', requiresAdmin: true },
      },

      {
        path: 'admin/export',
        name: 'AdminExport',
        component: () => import('@/views/admin/Export.vue'),
        meta: { title: '模型导出', requiresAdmin: true },
      },
      {
        path: 'admin/feedback',
        name: 'AdminFeedback',
        component: () => import('@/views/admin/Feedback.vue'),
        meta: { title: '反馈管理', requiresAdmin: true },
      },
    ],
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach(async (to, from, next) => {
  const token = localStorage.getItem('token')

  if (to.path === '/login' || to.path === '/register') {
    if (token) {
      next('/')
    } else {
      next()
    }
    return
  }

  if (to.matched.some((r) => r.meta.requiresAuth)) {
    if (!token) {
      next('/login')
      return
    }

    const { useUserStore } = await import('@/store/modules/user')
    const userStore = useUserStore()

    if (!userStore.userInfo) {
      try {
        await userStore.fetchUserInfo()
      } catch {
        userStore.logout()
        next('/login')
        return
      }
    }

    if (to.meta.requiresAdmin && userStore.userInfo?.role !== 'admin') {
      next('/')
      return
    }
  }

  next()
})

export default router
