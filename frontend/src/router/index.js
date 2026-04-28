import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

import RoleShell from '@/layouts/RoleShell.vue'
import Login from '@/views/Login.vue'
import Register from '@/views/Register.vue'
import AdminAnnouncements from '@/views/admin/AdminAnnouncements.vue'
import AdminComplaints from '@/views/admin/AdminComplaints.vue'
import AdminFinance from '@/views/admin/AdminFinance.vue'
import AdminHome from '@/views/admin/AdminHome.vue'
import AdminLogs from '@/views/admin/AdminLogs.vue'
import AdminProperties from '@/views/admin/AdminProperties.vue'
import AdminRepairs from '@/views/admin/AdminRepairs.vue'
import AdminUsers from '@/views/admin/AdminUsers.vue'
import FeedbackList from '@/views/employee/FeedbackList.vue'
import WorkOrders from '@/views/employee/WorkOrders.vue'
import Bills from '@/views/owner/Bills.vue'
import Complaints from '@/views/owner/Complaints.vue'
import News from '@/views/owner/News.vue'
import OwnerHome from '@/views/owner/OwnerHome.vue'
import Properties from '@/views/owner/Properties.vue'
import Repairs from '@/views/owner/Repairs.vue'
import Profile from '@/views/Profile.vue'
import RechargeResult from '@/views/recharge/Result.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    { path: '/', redirect: '/login' },
    { path: '/login', name: 'login', component: Login, meta: { public: true } },
    { path: '/register', name: 'register', component: Register, meta: { public: true } },
    { path: '/recharge/result', name: 'recharge-result', component: RechargeResult, meta: { public: true } },
    {
      path: '/owner',
      component: RoleShell,
      meta: { roles: ['owner'] },
      children: [
        { path: '', component: OwnerHome, meta: { title: '首页' } },
        { path: 'properties', component: Properties, meta: { title: '我的房产' } },
        { path: 'repairs', component: Repairs, meta: { title: '物业报修' } },
        { path: 'bills', component: Bills, meta: { title: '费用缴纳' } },
        { path: 'complaints', component: Complaints, meta: { title: '投诉建议' } },
        { path: 'news', component: News, meta: { title: '平台公告' } },
        { path: 'profile', component: Profile, meta: { title: '个人中心' } },
      ],
    },
    {
      path: '/employee',
      component: RoleShell,
      meta: { roles: ['employee'] },
      children: [
        { path: '', component: WorkOrders, meta: { title: '我的工单' } },
        { path: 'feedback', component: FeedbackList, meta: { title: '服务反馈' } },
        { path: 'profile', component: Profile, meta: { title: '个人中心' } },
      ],
    },
    {
      path: '/admin',
      component: RoleShell,
      meta: { roles: ['admin'] },
      children: [
        { path: '', component: AdminHome, meta: { title: '工作台' } },
        { path: 'users', component: AdminUsers, meta: { title: '用户管理' } },
        { path: 'properties', component: AdminProperties, meta: { title: '房产管理' } },
        { path: 'repairs', component: AdminRepairs, meta: { title: '工单管理' } },
        { path: 'complaints', component: AdminComplaints, meta: { title: '投诉管理' } },
        { path: 'finance', component: AdminFinance, meta: { title: '财务管理' } },
        { path: 'announcements', component: AdminAnnouncements, meta: { title: '公告管理' } },
        { path: 'logs', component: AdminLogs, meta: { title: '系统日志' } },
        { path: 'profile', component: Profile, meta: { title: '个人中心' } },
      ],
    },
  ],
})

router.beforeEach(async (to) => {
  const auth = useAuthStore()
  if (!auth.bootstrapped) {
    await auth.bootstrap()
  }
  if (to.meta.public) return true
  if (!auth.user) return { path: '/login' }
  if (to.meta.roles && !to.meta.roles.includes(auth.role)) {
    const needAdmin = to.meta.roles.includes('admin')
    const isAdminUser = auth.role === 'admin' || auth.user?.is_superuser
    if (needAdmin && isAdminUser) return true
    return { path: auth.redirectPathByRole() }
  }
  return true
})

export default router
