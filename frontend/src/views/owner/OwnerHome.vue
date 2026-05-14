<script setup>
import { computed, onMounted, ref } from 'vue'
import http from '@/api/http'
import { useAuthStore } from '@/stores/auth'
import { formatDateCN, statusLabel } from '@/utils/display'

const auth = useAuthStore()

const loading = ref(false)
const error = ref('')
const summary = ref({
  properties_total: 0,
  bills_unpaid: 0,
  bills_paid: 0,
  bills_overdue: 0,
  repairs_pending: 0,
  repairs_processing: 0,
  repairs_completed: 0,
  complaints_pending: 0,
  complaints_processing: 0,
  complaints_completed: 0,
  announcements_total: 0,
})
const latestBills = ref([])
const latestRepairs = ref([])
const latestAnnouncements = ref([])

const cards = computed(() => [
  { label: '我的房产', value: summary.value.properties_total, hint: '已绑定房屋数量' },
  { label: '待缴账单', value: summary.value.bills_unpaid, hint: `已缴 ${summary.value.bills_paid} · 逾期 ${summary.value.bills_overdue}` },
  { label: '工单处理', value: summary.value.repairs_processing, hint: `待处理 ${summary.value.repairs_pending} · 已完成 ${summary.value.repairs_completed}` },
  { label: '投诉建议', value: summary.value.complaints_processing, hint: `待处理 ${summary.value.complaints_pending} · 已完成 ${summary.value.complaints_completed}` },
  { label: '公告数量', value: summary.value.announcements_total, hint: '已发布公告总数' },
])

function piePath(cx, cy, r, startAngle, endAngle) {
  const toXY = (angle) => {
    const rad = ((angle - 90) * Math.PI) / 180
    return { x: cx + r * Math.cos(rad), y: cy + r * Math.sin(rad) }
  }
  const s = toXY(startAngle)
  const e = toXY(endAngle)
  const large = endAngle - startAngle <= 180 ? 0 : 1
  return `M ${cx} ${cy} L ${s.x} ${s.y} A ${r} ${r} 0 ${large} 1 ${e.x} ${e.y} Z`
}

const billSlices = computed(() => {
  const items = [
    { label: '未缴费', value: summary.value.bills_unpaid, color: '#2A6EBB' },
    { label: '已缴费', value: summary.value.bills_paid, color: '#16A34A' },
    { label: '已逾期', value: summary.value.bills_overdue, color: '#EA580C' },
  ]
  const total = items.reduce((s, i) => s + i.value, 0) || 1
  let start = -90
  return items.map((item) => {
    const sweep = (item.value / total) * 360
    const end = start + sweep
    const path = item.value ? piePath(50, 50, 38, start, end) : ''
    start = end
    return { ...item, path }
  })
})

const repairBars = computed(() => [
  { label: '待处理', value: summary.value.repairs_pending, color: '#2A6EBB' },
  { label: '处理中', value: summary.value.repairs_processing, color: '#EA580C' },
  { label: '已完成', value: summary.value.repairs_completed, color: '#16A34A' },
])

const complaintBars = computed(() => [
  { label: '待处理', value: summary.value.complaints_pending, color: '#7C3AED' },
  { label: '处理中', value: summary.value.complaints_processing, color: '#EA580C' },
  { label: '已完成', value: summary.value.complaints_completed, color: '#16A34A' },
])

const maxRepair = computed(() => Math.max(...repairBars.value.map((i) => i.value), 1))
const maxComplaint = computed(() => Math.max(...complaintBars.value.map((i) => i.value), 1))

async function load() {
  loading.value = true
  error.value = ''
  try {
    const [propsRes, unpaidRes, paidRes, overdueRes, repPendingRes, repProcRes, repDoneRes, compPendingRes, compProcRes, compDoneRes, annRes] =
      await Promise.all([
        http.get('/api/users/properties/my_properties/', { params: { page: 1, page_size: 1 } }),
        http.get('/api/finance/bills/', { params: { page: 1, page_size: 1, status: 'unpaid' } }),
        http.get('/api/finance/bills/', { params: { page: 1, page_size: 1, status: 'paid' } }),
        http.get('/api/finance/bills/', { params: { page: 1, page_size: 1, status: 'overdue' } }),
        http.get('/api/property/repairs/', { params: { page: 1, page_size: 1, status: 'pending' } }),
        http.get('/api/property/repairs/', { params: { page: 1, page_size: 1, status: 'processing' } }),
        http.get('/api/property/repairs/', { params: { page: 1, page_size: 1, status: 'completed' } }),
        http.get('/api/property/complaints/', { params: { page: 1, page_size: 1, status: 'pending' } }),
        http.get('/api/property/complaints/', { params: { page: 1, page_size: 1, status: 'processing' } }),
        http.get('/api/property/complaints/', { params: { page: 1, page_size: 1, status: 'completed' } }),
        http.get('/api/operation/announcements/platform/', { params: { page: 1, page_size: 1 } }),
      ])

    summary.value = {
      properties_total: propsRes.data?.count || 0,
      bills_unpaid: unpaidRes.data?.count || 0,
      bills_paid: paidRes.data?.count || 0,
      bills_overdue: overdueRes.data?.count || 0,
      repairs_pending: repPendingRes.data?.count || 0,
      repairs_processing: repProcRes.data?.count || 0,
      repairs_completed: repDoneRes.data?.count || 0,
      complaints_pending: compPendingRes.data?.count || 0,
      complaints_processing: compProcRes.data?.count || 0,
      complaints_completed: compDoneRes.data?.count || 0,
      announcements_total: annRes.data?.count || 0,
    }

    latestBills.value = unpaidRes.data?.results || []
    latestRepairs.value = repPendingRes.data?.results || []
    latestAnnouncements.value = annRes.data?.results || []
  } catch (e) {
    error.value = e.response?.data?.detail || e.message || '加载失败'
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>

<template>
  <div class="role-dashboard">
    <div class="rpms-panel role-dashboard__hero">
      <div class="role-dashboard__hero-top">
        <div>
          <p class="role-dashboard__eyebrow">业主看板</p>
          <h2 class="role-dashboard__title">欢迎，{{ auth.user?.username }}</h2>
          <p class="role-dashboard__subtitle">
            这里汇总您的房产、账单、报修和投诉状态，便于快速了解当前办理进度。
          </p>
        </div>
        <div class="role-dashboard__badge">业主数据看板</div>
      </div>
      <div v-if="loading" class="rpms-muted">正在加载数据...</div>
      <p v-else-if="error" class="rpms-msg--err">{{ error }}</p>
      <div class="role-dashboard__cards">
        <article v-for="card in cards" :key="card.label" class="role-dashboard__card">
          <p class="role-dashboard__card-label">{{ card.label }}</p>
          <strong class="role-dashboard__card-value">{{ card.value }}</strong>
          <span class="role-dashboard__card-hint">{{ card.hint }}</span>
        </article>
      </div>
    </div>

    <div class="role-dashboard__charts">
      <section class="rpms-panel role-dashboard__panel">
        <h3 class="role-dashboard__panel-title">账单状态环形图</h3>
        <div class="role-dashboard__pie-wrap">
          <svg viewBox="0 0 100 100" class="role-dashboard__pie" aria-label="账单状态环形图">
            <g v-for="slice in billSlices" :key="slice.label">
              <path v-if="slice.path" :d="slice.path" :fill="slice.color" />
            </g>
            <circle cx="50" cy="50" r="20" fill="#fff" />
            <text x="50" y="47" text-anchor="middle" fill="#0f172a" font-size="10" font-weight="700">
              {{ summary.bills_unpaid }}
            </text>
            <text x="50" y="58" text-anchor="middle" fill="#64748b" font-size="8">待缴</text>
          </svg>
          <div class="role-dashboard__legend">
            <div v-for="item in billSlices" :key="item.label" class="role-dashboard__legend-item">
              <span class="role-dashboard__dot" :style="{ background: item.color }" />
              <span>{{ item.label }}</span>
              <strong>{{ item.value }}</strong>
            </div>
          </div>
        </div>
      </section>

      <section class="rpms-panel role-dashboard__panel">
        <h3 class="role-dashboard__panel-title">工单状态条形图</h3>
        <div class="role-dashboard__bar-list">
          <div v-for="item in repairBars" :key="item.label" class="role-dashboard__bar-row">
            <div class="role-dashboard__bar-meta">
              <span>{{ item.label }}</span>
              <strong>{{ item.value }}</strong>
            </div>
            <div class="role-dashboard__bar-track">
              <div class="role-dashboard__bar-fill" :style="{ width: `${(item.value / maxRepair) * 100}%`, background: item.color }" />
            </div>
          </div>
        </div>
      </section>

      <section class="rpms-panel role-dashboard__panel">
        <h3 class="role-dashboard__panel-title">投诉状态条形图</h3>
        <div class="role-dashboard__bar-list">
          <div v-for="item in complaintBars" :key="item.label" class="role-dashboard__bar-row">
            <div class="role-dashboard__bar-meta">
              <span>{{ item.label }}</span>
              <strong>{{ item.value }}</strong>
            </div>
            <div class="role-dashboard__bar-track">
              <div class="role-dashboard__bar-fill" :style="{ width: `${(item.value / maxComplaint) * 100}%`, background: item.color }" />
            </div>
          </div>
        </div>
      </section>

      <section class="rpms-panel role-dashboard__panel role-dashboard__panel--wide">
        <h3 class="role-dashboard__panel-title">待办与公告</h3>
        <div class="role-dashboard__lists">
          <div>
            <p class="role-dashboard__mini-title">待缴账单</p>
            <ul class="role-dashboard__mini-list">
              <li v-for="b in latestBills" :key="b.id">
                <span>#{{ b.id }} · {{ b.year_month }}</span>
                <strong>{{ b.amount }}</strong>
              </li>
              <li v-if="!latestBills.length" class="rpms-muted">暂无待缴账单</li>
            </ul>
          </div>
          <div>
            <p class="role-dashboard__mini-title">待处理工单</p>
            <ul class="role-dashboard__mini-list">
              <li v-for="r in latestRepairs" :key="r.id">
                <span>#{{ r.id }} · {{ statusLabel(r.status) }}</span>
                <strong>{{ formatDateCN(r.created_at) }}</strong>
              </li>
              <li v-if="!latestRepairs.length" class="rpms-muted">暂无待处理工单</li>
            </ul>
          </div>
          <div>
            <p class="role-dashboard__mini-title">最新公告</p>
            <ul class="role-dashboard__mini-list">
              <li v-for="a in latestAnnouncements" :key="a.id">
                <span>{{ a.title }}</span>
                <strong>{{ formatDateCN(a.publish_time || a.created_at) }}</strong>
              </li>
              <li v-if="!latestAnnouncements.length" class="rpms-muted">暂无公告</li>
            </ul>
          </div>
        </div>
      </section>
    </div>
  </div>
</template>

<style scoped>
.role-dashboard {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.role-dashboard__hero {
  background: linear-gradient(135deg, rgba(42, 110, 187, 0.08), rgba(255, 255, 255, 0.96));
}

.role-dashboard__hero-top {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: flex-start;
  margin-bottom: 18px;
}

.role-dashboard__eyebrow {
  margin: 0 0 8px;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.12em;
  color: var(--rpms-primary, #2a6ebb);
}

.role-dashboard__title {
  margin: 0 0 10px;
  font-size: 1.5rem;
  font-weight: 800;
  color: var(--rpms-text, #0f172a);
}

.role-dashboard__subtitle {
  margin: 0;
  color: var(--rpms-text-muted, #64748b);
  line-height: 1.7;
}

.role-dashboard__badge {
  padding: 8px 14px;
  border-radius: 999px;
  background: rgba(42, 110, 187, 0.1);
  color: var(--rpms-primary, #2a6ebb);
  font-size: 13px;
  font-weight: 600;
}

.role-dashboard__cards {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 14px;
}

.role-dashboard__card {
  padding: 16px;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.86);
  border: 1px solid rgba(226, 232, 240, 0.95);
  box-shadow: 0 8px 24px rgba(15, 23, 42, 0.05);
}

.role-dashboard__card-label {
  margin: 0 0 8px;
  font-size: 12px;
  color: var(--rpms-text-muted, #64748b);
}

.role-dashboard__card-value {
  display: block;
  margin-bottom: 8px;
  font-size: 1.45rem;
  color: var(--rpms-text, #0f172a);
}

.role-dashboard__card-hint {
  font-size: 12px;
  color: #64748b;
  line-height: 1.5;
}

.role-dashboard__charts {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 20px;
}

.role-dashboard__panel {
  min-height: 290px;
}

.role-dashboard__panel--wide {
  grid-column: 1 / -1;
}

.role-dashboard__panel-title {
  margin: 0 0 14px;
  font-size: 1rem;
  font-weight: 700;
  color: var(--rpms-text, #0f172a);
}

.role-dashboard__pie-wrap {
  display: flex;
  align-items: center;
  gap: 16px;
}

.role-dashboard__pie {
  width: 170px;
  height: 170px;
  flex-shrink: 0;
  filter: drop-shadow(0 10px 22px rgba(15, 23, 42, 0.08));
}

.role-dashboard__legend {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.role-dashboard__legend-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  padding: 8px 10px;
  border-radius: 12px;
  border: 1px solid rgba(226, 232, 240, 0.9);
  background: #f8fafc;
  font-size: 13px;
}

.role-dashboard__legend-item span {
  flex: 1;
}

.role-dashboard__dot {
  width: 10px;
  height: 10px;
  border-radius: 999px;
  flex-shrink: 0;
}

.role-dashboard__bar-list {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.role-dashboard__bar-row {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.role-dashboard__bar-meta {
  display: flex;
  justify-content: space-between;
  gap: 10px;
  font-size: 13px;
}

.role-dashboard__bar-track {
  height: 14px;
  border-radius: 999px;
  background: #eef2f7;
  overflow: hidden;
}

.role-dashboard__bar-fill {
  height: 100%;
  border-radius: inherit;
}

.role-dashboard__lists {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 16px;
}

.role-dashboard__mini-title {
  margin: 0 0 10px;
  font-size: 13px;
  font-weight: 700;
  color: var(--rpms-primary, #2a6ebb);
}

.role-dashboard__mini-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.role-dashboard__mini-list li {
  display: flex;
  justify-content: space-between;
  gap: 10px;
  font-size: 13px;
  color: var(--rpms-text, #0f172a);
  padding: 8px 10px;
  border-radius: 12px;
  background: #f8fafc;
  border: 1px solid rgba(226, 232, 240, 0.9);
}

@media (max-width: 1200px) {
  .role-dashboard__cards,
  .role-dashboard__charts,
  .role-dashboard__lists {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 760px) {
  .role-dashboard__hero-top,
  .role-dashboard__pie-wrap {
    flex-direction: column;
  }

  .role-dashboard__cards,
  .role-dashboard__charts,
  .role-dashboard__lists {
    grid-template-columns: 1fr;
  }
}
</style>
