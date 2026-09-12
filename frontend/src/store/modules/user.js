import { defineStore } from 'pinia'
import { login, register, getUserInfo } from '@/api/auth'

export const useUserStore = defineStore('user', {
  state: () => ({
    token: localStorage.getItem('token') || '',
    userInfo: null,
  }),

  getters: {
    isLoggedIn: (state) => !!state.token,
    isAdmin: (state) => state.userInfo?.role === 'admin',
    username: (state) => state.userInfo?.username || '',
  },

  actions: {
    async loginAction(username, password) {
      const res = await login(username, password)
      this.token = res.data.access_token
      localStorage.setItem('token', this.token)
      await this.fetchUserInfo()
    },

    async registerAction(data) {
      return await register(data)
    },

    async fetchUserInfo() {
      const res = await getUserInfo()
      this.userInfo = res.data
    },

    logout() {
      this.token = ''
      this.userInfo = null
      localStorage.removeItem('token')
    },
  },
})
