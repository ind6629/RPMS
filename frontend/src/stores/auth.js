import { defineStore } from 'pinia'
import http, { ensureCsrf } from '@/api/http'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: null,
    role: null,
    bootstrapped: false,
  }),
  actions: {
    async bootstrap() {
      await ensureCsrf()
      try {
        const { data } = await http.get('/api/users/accounts/me/')
        this.user = data
        this.role = data.role
      } catch {
        this.user = null
        this.role = null
      }
      this.bootstrapped = true
    },
    async login(payload) {
      await ensureCsrf()
      const { data } = await http.post('/api/users/login/', payload)
      this.user = data.user
      this.role = data.role
      return data
    },
    async register(payload) {
      await ensureCsrf()
      const { data } = await http.post('/api/users/register/', payload)
      return data
    },
    async logout() {
      try {
        await http.post('/api/users/logout/')
      } catch {
        // 后端登出失败时也允许前端强制退出，避免界面卡在已登录态
      } finally {
        this.user = null
        this.role = null
        this.bootstrapped = true
      }
    },
    redirectPathByRole() {
      if (this.role === 'admin' || this.user?.is_superuser) return '/admin'
      if (this.role === 'employee') return '/employee'
      return '/owner'
    },
  },
})
