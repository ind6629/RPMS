<script setup>
import { computed, ref, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import NavIcon from '@/components/NavIcon.vue'

const auth = useAuthStore()
const router = useRouter()
const route = useRoute()

const SIDEBAR_KEY = 'rpms-sidebar-collapsed'
const sidebarCollapsed = ref(
  typeof localStorage !== 'undefined' && localStorage.getItem(SIDEBAR_KEY) === '1',
)

watch(sidebarCollapsed, (v) => {
  if (typeof localStorage !== 'undefined') {
    localStorage.setItem(SIDEBAR_KEY, v ? '1' : '0')
  }
})

function toggleSidebar() {
  sidebarCollapsed.value = !sidebarCollapsed.value
}

const isAdmin = computed(() => auth.role === 'admin' || auth.user?.is_superuser)

const appName = computed(() => {
  if (isAdmin.value) return '物业后台'
  if (auth.role === 'employee') return '员工工作台'
  return '业主服务'
})

const pageTitle = computed(() => {
  const m = route.matched.map((r) => r.meta?.title).filter(Boolean)
  return m.length ? m[m.length - 1] : '首页'
})

const ownerMenu = [
  { to: '/owner', title: '首页', icon: 'home', end: true },
  { to: '/owner/properties', title: '我的房产', icon: 'properties' },
  { to: '/owner/repairs', title: '物业报修', icon: 'repairs' },
  { to: '/owner/bills', title: '费用缴纳', icon: 'bills' },
  { to: '/owner/complaints', title: '投诉建议', icon: 'complaints' },
  { to: '/owner/news', title: '平台公告', icon: 'news' },
  { to: '/owner/profile', title: '个人中心', icon: 'profile' },
]

const employeeMenu = [
  { to: '/employee', title: '我的工单', icon: 'clipboard', end: true },
  { to: '/employee/feedback', title: '服务反馈', icon: 'star' },
  { to: '/employee/profile', title: '个人中心', icon: 'profile' },
]

const adminMenu = [
  { to: '/admin', title: '工作台', icon: 'home', end: true },
  { to: '/admin/users', title: '用户管理', icon: 'users' },
  { to: '/admin/properties', title: '房产管理', icon: 'properties' },
  { to: '/admin/repairs', title: '工单管理', icon: 'repairs' },
  { to: '/admin/complaints', title: '投诉管理', icon: 'complaints' },
  { to: '/admin/finance', title: '财务管理', icon: 'bills' },
  { to: '/admin/announcements', title: '公告管理', icon: 'news' },
  { to: '/admin/logs', title: '系统日志', icon: 'logs' },
  { to: '/admin/profile', title: '个人中心', icon: 'profile' },
]

const menu = computed(() => {
  if (isAdmin.value) return adminMenu
  if (auth.role === 'employee') return employeeMenu
  return ownerMenu
})

async function onLogout() {
  try {
    await auth.logout()
  } finally {
    router.replace('/login')
  }
}
</script>

<template>
  <div class="rpms-app" :class="{ 'rpms-app--sidebar-collapsed': sidebarCollapsed }">
    <aside class="rpms-sidebar" :class="{ 'rpms-sidebar--collapsed': sidebarCollapsed }">
      <div class="rpms-sidebar__head">
        <div class="rpms-sidebar__brand">
          <span class="rpms-sidebar__logo">RPMS</span>
          <span class="rpms-sidebar__sub">{{ appName }}</span>
        </div>
        <button
          type="button"
          class="rpms-sidebar__collapse-btn"
          :title="sidebarCollapsed ? '展开菜单' : '收起菜单'"
          :aria-expanded="!sidebarCollapsed"
          aria-label="切换侧边栏"
          @click="toggleSidebar"
        >
          <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2.25">
            <path
              v-if="!sidebarCollapsed"
              d="M15 6l-6 6 6 6"
              stroke-linecap="round"
              stroke-linejoin="round"
            />
            <path v-else d="M9 18l6-6-6-6" stroke-linecap="round" stroke-linejoin="round" />
          </svg>
        </button>
      </div>
      <nav class="rpms-nav" aria-label="主导航">
        <RouterLink
          v-for="item in menu"
          :key="item.to"
          :to="item.to"
          :end="Boolean(item.end)"
          class="rpms-nav__link"
          active-class="rpms-nav__link--active"
          :title="sidebarCollapsed ? item.title : undefined"
        >
          <NavIcon :name="item.icon" />
          <span class="rpms-nav__text">{{ item.title }}</span>
        </RouterLink>
      </nav>
      <div class="rpms-sidebar__foot">
        <div class="rpms-sidebar__user">
          <span class="rpms-sidebar__avatar" aria-hidden="true">{{
            (auth.user?.username || '?').slice(0, 1).toUpperCase()
          }}</span>
          <div class="rpms-sidebar__user-meta">
            <span class="rpms-sidebar__user-name">{{ auth.user?.username }}</span>
            <span class="rpms-sidebar__user-role">{{ auth.role }}</span>
          </div>
        </div>
        <button type="button" class="rpms-sidebar__logout" @click="onLogout">退出登录</button>
      </div>
    </aside>
    <div class="rpms-content-col">
      <header class="rpms-topbar">
        <div class="rpms-topbar__inner">
          <h1 class="rpms-topbar__title">{{ pageTitle }}</h1>
          <p class="rpms-topbar__hint">左侧菜单可折叠；列表底部支持分页与每页条数</p>
        </div>
      </header>
      <main class="rpms-main">
        <RouterView :key="route.fullPath" />
      </main>
    </div>
  </div>
</template>

<style scoped>
.rpms-app {
  display: flex;
  min-height: 100vh;
  color: var(--rpms-text, #0f172a);
}

.rpms-sidebar {
  width: 260px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  background: linear-gradient(180deg, rgba(15, 23, 42, 0.92) 0%, rgba(15, 23, 42, 0.98) 100%);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  color: #e2e8f0;
  border-right: 1px solid rgba(148, 163, 184, 0.12);
  box-shadow: 4px 0 24px rgba(15, 23, 42, 0.12);
  transition: width 0.28s cubic-bezier(0.4, 0, 0.2, 1);
}

.rpms-sidebar--collapsed {
  width: 76px;
}

.rpms-sidebar__head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 8px;
  padding: 20px 16px 14px;
  border-bottom: 1px solid rgba(148, 163, 184, 0.1);
}

.rpms-sidebar__brand {
  min-width: 0;
  overflow: hidden;
}

.rpms-sidebar--collapsed .rpms-sidebar__brand {
  text-align: center;
}

.rpms-sidebar__logo {
  display: block;
  font-size: 1.25rem;
  font-weight: 800;
  letter-spacing: 0.08em;
  color: #f8fafc;
  background: linear-gradient(135deg, #fff 0%, #94a3b8 100%);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
}

.rpms-sidebar__sub {
  display: block;
  margin-top: 6px;
  font-size: 12px;
  color: var(--rpms-sidebar-text, #94a3b8);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.rpms-sidebar--collapsed .rpms-sidebar__sub {
  display: none;
}

.rpms-sidebar__collapse-btn {
  flex-shrink: 0;
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px solid rgba(148, 163, 184, 0.2);
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.06);
  color: #cbd5e1;
  cursor: pointer;
  transition:
    background 0.2s,
    border-color 0.2s,
    transform 0.15s;
}

.rpms-sidebar__collapse-btn:hover {
  background: rgba(42, 110, 187, 0.35);
  border-color: rgba(42, 110, 187, 0.5);
  color: #fff;
}

.rpms-sidebar__collapse-btn:active {
  transform: scale(0.96);
}

.rpms-sidebar--collapsed .rpms-sidebar__collapse-btn {
  margin: 0 auto;
}

.rpms-sidebar--collapsed .rpms-sidebar__head {
  flex-direction: column;
  align-items: center;
}

.rpms-nav {
  flex: 1;
  padding: 12px 10px;
  overflow-y: auto;
}

.rpms-nav__link {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 11px 14px;
  margin-bottom: 4px;
  border-radius: 14px;
  color: var(--rpms-sidebar-text, #94a3b8);
  text-decoration: none;
  font-size: 14px;
  font-weight: 500;
  transition:
    background 0.2s,
    color 0.2s,
    transform 0.15s,
    box-shadow 0.2s;
}

.rpms-nav__link:hover {
  background: rgba(255, 255, 255, 0.08);
  color: #f1f5f9;
}

.rpms-nav__link:active {
  transform: scale(0.98);
}

.rpms-nav__link--active {
  background: linear-gradient(135deg, rgba(42, 110, 187, 0.45) 0%, rgba(42, 110, 187, 0.2) 100%);
  color: #fff;
  box-shadow: 0 4px 14px rgba(42, 110, 187, 0.25);
  border: 1px solid rgba(255, 255, 255, 0.08);
}

.rpms-nav__link--active :deep(.rpms-nav-icon) {
  color: #fff;
}

.rpms-sidebar--collapsed .rpms-nav__link {
  justify-content: center;
  padding: 12px;
}

.rpms-sidebar--collapsed .rpms-nav__text {
  display: none;
}

.rpms-sidebar__foot {
  padding: 14px 12px 16px;
  border-top: 1px solid rgba(148, 163, 184, 0.1);
}

.rpms-sidebar__user {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 12px;
}

.rpms-sidebar--collapsed .rpms-sidebar__user {
  flex-direction: column;
  text-align: center;
}

.rpms-sidebar__avatar {
  width: 40px;
  height: 40px;
  border-radius: 12px;
  background: linear-gradient(135deg, var(--rpms-primary, #2a6ebb), #1d4d82);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 15px;
  font-weight: 700;
  flex-shrink: 0;
  box-shadow: 0 4px 12px rgba(42, 110, 187, 0.35);
}

.rpms-sidebar__user-meta {
  min-width: 0;
  flex: 1;
}

.rpms-sidebar--collapsed .rpms-sidebar__user-meta {
  display: none;
}

.rpms-sidebar__user-name {
  display: block;
  font-size: 13px;
  font-weight: 600;
  color: #f1f5f9;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.rpms-sidebar__user-role {
  font-size: 11px;
  color: var(--rpms-sidebar-text, #94a3b8);
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.rpms-sidebar__logout {
  width: 100%;
  padding: 10px 12px;
  border-radius: 12px;
  border: 1px solid rgba(248, 113, 113, 0.35);
  background: rgba(248, 113, 113, 0.08);
  color: #fecaca;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition:
    background 0.2s,
    border-color 0.2s,
    transform 0.15s;
}

.rpms-sidebar__logout:hover {
  background: rgba(248, 113, 113, 0.18);
  border-color: rgba(248, 113, 113, 0.55);
  color: #fff;
}

.rpms-sidebar__logout:active {
  transform: scale(0.98);
}

.rpms-sidebar--collapsed .rpms-sidebar__logout {
  font-size: 0;
  padding: 10px;
  position: relative;
}

.rpms-sidebar--collapsed .rpms-sidebar__logout::after {
  content: '退';
  font-size: 13px;
  font-weight: 600;
}

.rpms-content-col {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  background: var(--rpms-main-bg);
}

.rpms-topbar {
  flex-shrink: 0;
  padding: 0 28px;
  min-height: 64px;
  display: flex;
  align-items: center;
  background: rgba(255, 255, 255, 0.72);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border-bottom: 1px solid rgba(226, 232, 240, 0.9);
  box-shadow: 0 1px 0 rgba(255, 255, 255, 0.8) inset;
}

.rpms-topbar__inner {
  display: flex;
  flex-wrap: wrap;
  align-items: baseline;
  gap: 12px 20px;
  width: 100%;
  padding: 16px 0;
}

.rpms-topbar__title {
  margin: 0;
  font-size: 1.28rem;
  font-weight: 700;
  letter-spacing: -0.02em;
  color: var(--rpms-text);
}

.rpms-topbar__hint {
  margin: 0;
  font-size: 13px;
  color: var(--rpms-text-muted);
}

@media (max-width: 900px) {
  .rpms-topbar__hint {
    display: none;
  }
}
</style>
