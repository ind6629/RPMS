<script setup>
import { computed, onMounted, ref } from 'vue'
import http from '@/api/http'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()

const loading = ref(false)
const error = ref('')
const dashboard = ref(null)

const palette = ['#2A6EBB', '#16A34A', '#EA580C', '#7C3AED', '#14B8A6', '#EF4444']

const summaryCards = computed(() => {
  const s = dashboard.value?.summary || {}
  return [
    { label: '用户总数', value: s.users_total || 0, hint: `业主 ${s.owners_total || 0} · 员工 ${s.employees_total || 0}` },
    { label: '房产总数', value: s.properties_total || 0, hint: `房屋 ${s.rooms_total || 0}` },
    { label: '已绑定房屋', value: s.rooms_bound || 0, hint: `未绑定 ${s.rooms_unbound || 0}` },
    { label: '报修工单', value: s.repairs_total || 0, hint: `处理中 ${s.repairs_processing || 0} · 已完成 ${s.repairs_completed || 0}` },
    { label: '投诉建议', value: s.complaints_total || 0, hint: `处理中 ${s.complaints_processing || 0} · 已完成 ${s.complaints_completed || 0}` },
    { label: '账单总数', value: s.bills_total || 0, hint: `已缴 ${s.bills_paid || 0} · 未缴 ${s.bills_unpaid || 0} · 逾期 ${s.bills_overdue || 0}` },
  ]
})

const repairTrend = computed(() => dashboard.value?.repair_trend || [])
const financeTrend = computed(() => dashboard.value?.finance_trend || [])
const complaintTypes = computed(() => dashboard.value?.complaint_types || [])
const propertyBinding = computed(() => dashboard.value?.property_binding || [])
const employeeRanking = computed(() => dashboard.value?.employee_ranking || [])

const maxRepair = computed(() => Math.max(...repairTrend.value.map((i) => Number(i.value) || 0), 1))
const maxFinance = computed(() => Math.max(...financeTrend.value.map((i) => Number(i.value) || 0), 1))
const maxEmployee = computed(() => Math.max(...employeeRanking.value.map((i) => Number(i.value) || 0), 1))

function fmt(v) {
  return new Intl.NumberFormat('zh-CN', { maximumFractionDigits: 2 }).format(Number(v) || 0)
}

function monthLabel(v) {
  if (!v) return '--'
  const parts = String(v).split('-')
  return parts.length === 2 ? `${parts[1]}月` : String(v)
}

function getLinePath(list, width = 100, height = 100, padding = 14) {
  const points = list.map((item, idx) => ({
    x: padding + ((width - padding * 2) * idx) / Math.max(list.length - 1, 1),
    y: height - padding - ((Number(item.value) || 0) / maxRepair.value) * (height - padding * 2),
  }))
  if (!points.length) return ''
  return points.map((p, idx) => `${idx === 0 ? 'M' : 'L'} ${p.x} ${p.y}`).join(' ')
}

function getLineAreaPath(list, width = 100, height = 100, padding = 14) {
  const points = list.map((item, idx) => ({
    x: padding + ((width - padding * 2) * idx) / Math.max(list.length - 1, 1),
    y: height - padding - ((Number(item.value) || 0) / maxRepair.value) * (height - padding * 2),
  }))
  if (!points.length) return ''
  const first = points[0]
  const last = points[points.length - 1]
  return [
    `M ${first.x} ${height - padding}`,
    ...points.map((p) => `L ${p.x} ${p.y}`),
    `L ${last.x} ${height - padding}`,
    'Z',
  ].join(' ')
}

function polarToCartesian(cx, cy, r, angleDeg) {
  const angle = ((angleDeg - 90) * Math.PI) / 180
  return {
    x: cx + r * Math.cos(angle),
    y: cy + r * Math.sin(angle),
  }
}

function donutSlicePath(cx, cy, outerR, innerR, startAngle, endAngle) {
  const startOuter = polarToCartesian(cx, cy, outerR, endAngle)
  const endOuter = polarToCartesian(cx, cy, outerR, startAngle)
  const startInner = polarToCartesian(cx, cy, innerR, startAngle)
  const endInner = polarToCartesian(cx, cy, innerR, endAngle)
  const largeArc = endAngle - startAngle <= 180 ? 0 : 1
  return [
    `M ${startOuter.x} ${startOuter.y}`,
    `A ${outerR} ${outerR} 0 ${largeArc} 0 ${endOuter.x} ${endOuter.y}`,
    `L ${startInner.x} ${startInner.y}`,
    `A ${innerR} ${innerR} 0 ${largeArc} 1 ${endInner.x} ${endInner.y}`,
    'Z',
  ].join(' ')
}

function buildSlices(list, outerR = 40, innerR = 26) {
  const total = list.reduce((sum, item) => sum + (Number(item.value) || 0), 0)
  let start = -90
  return list.map((item, idx) => {
    const value = Number(item.value) || 0
    const sweep = total ? (value / total) * 360 : 0
    const end = start + sweep
    const slice = {
      label: item.label,
      value,
      color: palette[idx % palette.length],
      path: value > 0 ? donutSlicePath(50, 50, outerR, innerR, start, end) : '',
    }
    start = end
    return slice
  })
}

const complaintSlices = computed(() => buildSlices(complaintTypes.value))
const bindingSlices = computed(() => buildSlices(propertyBinding.value, 38, 22))

const financeBars = computed(() =>
  financeTrend.value.map((item, idx) => ({
    label: monthLabel(item.label),
    value: Number(item.value) || 0,
    color: palette[idx % palette.length],
  })),
)

const rankRows = computed(() =>
  employeeRanking.value.map((item, idx) => ({
    label: item.label,
    value: Number(item.value) || 0,
    color: palette[idx % palette.length],
  })),
)

async function loadDashboard() {
  loading.value = true
  error.value = ''
  try {
    const { data } = await http.get('/api/operation/dashboard/summary/')
    dashboard.value = data
  } catch (e) {
    error.value = e.response?.data?.detail || e.message || '统计数据加载失败'
  } finally {
    loading.value = false
  }
}

onMounted(loadDashboard)
</script>

<template>
  <div class="admin-home">
    <div class="admin-home__hero rpms-panel">
      <div class="admin-home__hero-top">
        <div>
          <p class="admin-home__eyebrow">ADMIN DASHBOARD</p>
          <h2 class="admin-home__title">欢迎，{{ auth.user?.username }}</h2>
          <p class="admin-home__subtitle">
            这里集中展示用户、房产、工单、财务、投诉与系统运行概况，帮助你快速掌握物业管理状态。
          </p>
        </div>
        <div class="admin-home__hero-badge">
          <span class="admin-home__dot" />
          实时统计看板
        </div>
      </div>

      <div v-if="loading" class="rpms-muted">正在加载统计数据...</div>
      <p v-else-if="error" class="rpms-msg--err">{{ error }}</p>

      <div class="admin-home__summary-grid">
        <article v-for="card in summaryCards" :key="card.label" class="admin-home__summary-card">
          <p class="admin-home__summary-label">{{ card.label }}</p>
          <strong class="admin-home__summary-value">{{ card.value }}</strong>
          <span class="admin-home__summary-hint">{{ card.hint }}</span>
        </article>
      </div>
    </div>

    <div class="admin-home__charts">
      <section class="rpms-panel admin-home__chart admin-home__chart--wide">
        <div class="admin-home__chart-head">
          <div>
            <h3 class="admin-home__chart-title">工单趋势折线图</h3>
            <p class="admin-home__chart-subtitle">近 6 个月报修工单数量变化</p>
          </div>
        </div>
        <svg class="admin-home__line" viewBox="0 0 360 210" preserveAspectRatio="none" aria-label="工单趋势折线图">
          <defs>
            <linearGradient id="repairArea" x1="0" x2="0" y1="0" y2="1">
              <stop offset="0%" stop-color="#2A6EBB" stop-opacity="0.28" />
              <stop offset="100%" stop-color="#2A6EBB" stop-opacity="0.02" />
            </linearGradient>
          </defs>
          <path
            d="M 28 28 L 332 28 M 28 76 L 332 76 M 28 124 L 332 124 M 28 172 L 332 172"
            stroke="#e2e8f0"
            stroke-width="1"
            stroke-dasharray="3 4"
          />
          <path
            v-if="repairTrend.length"
            :d="getLinePath(repairTrend, 360, 180, 28)"
            fill="none"
            stroke="#2A6EBB"
            stroke-width="3"
            stroke-linecap="round"
            stroke-linejoin="round"
          />
          <path
            v-if="repairTrend.length"
            :d="getLineAreaPath(repairTrend, 360, 180, 28)"
            fill="url(#repairArea)"
            opacity="0.18"
          />
          <g v-for="(item, idx) in repairTrend" :key="item.label">
            <circle
              :cx="28 + ((304) * idx) / Math.max(repairTrend.length - 1, 1)"
              :cy="180 - 28 - ((Number(item.value) || 0) / maxRepair) * 124"
              r="4.5"
              fill="#2A6EBB"
            />
            <text
              :x="28 + ((304) * idx) / Math.max(repairTrend.length - 1, 1)"
              y="184"
              text-anchor="end"
              fill="#64748b"
              font-size="11"
              class="admin-home__trend-label"
              :transform="`rotate(-30 ${28 + ((304) * idx) / Math.max(repairTrend.length - 1, 1)} 184)`"
            >
              {{ monthLabel(item.label) }}
            </text>
          </g>
        </svg>
      </section>

      <section class="rpms-panel admin-home__chart">
        <div class="admin-home__chart-head">
          <div>
            <h3 class="admin-home__chart-title">财务收缴柱状图</h3>
            <p class="admin-home__chart-subtitle">近 6 个月支付金额趋势</p>
          </div>
        </div>
        <div class="admin-home__bars">
          <div v-for="bar in financeBars" :key="bar.label" class="admin-home__bar-item">
            <div class="admin-home__bar-top">
              <span>{{ bar.label }}</span>
              <strong>{{ fmt(bar.value) }}</strong>
            </div>
            <div class="admin-home__bar-track">
              <div
                class="admin-home__bar-fill"
                :style="{ height: `${(bar.value / maxFinance) * 100}%`, background: bar.color }"
              />
            </div>
          </div>
        </div>
      </section>

      <section class="rpms-panel admin-home__chart">
        <div class="admin-home__chart-head">
          <div>
            <h3 class="admin-home__chart-title">投诉类型饼图</h3>
            <p class="admin-home__chart-subtitle">投诉类别分布</p>
          </div>
        </div>
        <div class="admin-home__pie-wrap">
          <svg class="admin-home__pie" viewBox="0 0 100 100" aria-label="投诉类型饼图">
            <g v-for="slice in complaintSlices" :key="slice.label">
              <path v-if="slice.path" :d="slice.path" :fill="slice.color" />
            </g>
            <circle cx="50" cy="50" r="22" fill="#fff" />
            <text x="50" y="47" text-anchor="middle" fill="#0f172a" font-size="10" font-weight="700">投诉</text>
            <text x="50" y="58" text-anchor="middle" fill="#64748b" font-size="8">类型</text>
          </svg>
          <ul class="admin-home__legend">
            <li v-for="(item, idx) in complaintTypes" :key="item.label">
              <span class="admin-home__legend-dot" :style="{ background: palette[idx % palette.length] }" />
              <span>{{ item.label }}</span>
              <strong>{{ item.value }}</strong>
            </li>
          </ul>
        </div>
      </section>

      <section class="rpms-panel admin-home__chart">
        <div class="admin-home__chart-head">
          <div>
            <h3 class="admin-home__chart-title">房产绑定环形图</h3>
            <p class="admin-home__chart-subtitle">已绑定与未绑定房屋占比</p>
          </div>
        </div>
        <div class="admin-home__donut-wrap">
          <svg class="admin-home__donut" viewBox="0 0 100 100" aria-label="房产绑定环形图">
            <g v-for="slice in bindingSlices" :key="slice.label">
              <path v-if="slice.path" :d="slice.path" :fill="slice.color" />
            </g>
            <circle cx="50" cy="50" r="18" fill="#fff" />
            <text x="50" y="47" text-anchor="middle" fill="#0f172a" font-size="10" font-weight="700">
              {{ dashboard?.summary?.rooms_bound || 0 }}
            </text>
            <text x="50" y="58" text-anchor="middle" fill="#64748b" font-size="8">已绑定</text>
          </svg>
          <div class="admin-home__ring-legend">
            <div v-for="(item, idx) in propertyBinding" :key="item.label" class="admin-home__ring-item">
              <span class="admin-home__legend-dot" :style="{ background: palette[idx % palette.length] }" />
              <span>{{ item.label }}</span>
              <strong>{{ item.value }}</strong>
            </div>
          </div>
        </div>
      </section>

      <section class="rpms-panel admin-home__chart admin-home__chart--wide">
        <div class="admin-home__chart-head">
          <div>
            <h3 class="admin-home__chart-title">员工处理排行条形图</h3>
            <p class="admin-home__chart-subtitle">按已完成工单数量排行</p>
          </div>
        </div>
        <div class="admin-home__rank-list">
          <div v-for="(row, idx) in rankRows" :key="row.label" class="admin-home__rank-item">
            <div class="admin-home__rank-meta">
              <span class="admin-home__rank-index">{{ idx + 1 }}</span>
              <span class="admin-home__rank-name">{{ row.label }}</span>
              <strong class="admin-home__rank-value">{{ row.value }}</strong>
            </div>
            <div class="admin-home__rank-track">
              <div
                class="admin-home__rank-fill"
                :style="{ width: `${(row.value / maxEmployee) * 100}%`, background: row.color }"
              />
            </div>
          </div>
        </div>
      </section>
    </div>
  </div>
</template>

<style scoped>
.admin-home {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.admin-home__hero {
  background: linear-gradient(135deg, rgba(42, 110, 187, 0.08), rgba(255, 255, 255, 0.96));
}

.admin-home__hero-top {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 18px;
}

.admin-home__eyebrow {
  margin: 0 0 8px;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.12em;
  color: var(--rpms-primary, #2a6ebb);
}

.admin-home__title {
  margin: 0 0 10px;
  font-size: 1.5rem;
  font-weight: 800;
  color: var(--rpms-text, #0f172a);
}

.admin-home__subtitle {
  margin: 0;
  max-width: 820px;
  color: var(--rpms-text-muted, #64748b);
  line-height: 1.7;
}

.admin-home__hero-badge {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 8px 14px;
  border-radius: 999px;
  background: rgba(42, 110, 187, 0.1);
  color: var(--rpms-primary, #2a6ebb);
  font-size: 13px;
  font-weight: 600;
  white-space: nowrap;
}

.admin-home__dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #16a34a;
  box-shadow: 0 0 0 4px rgba(22, 163, 74, 0.12);
}

.admin-home__summary-grid {
  display: grid;
  grid-template-columns: repeat(6, minmax(0, 1fr));
  gap: 14px;
}

.admin-home__summary-card {
  padding: 16px 16px 14px;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.82);
  border: 1px solid rgba(226, 232, 240, 0.95);
  box-shadow: 0 8px 24px rgba(15, 23, 42, 0.05);
}

.admin-home__summary-label {
  margin: 0 0 8px;
  font-size: 12px;
  color: var(--rpms-text-muted, #64748b);
}

.admin-home__summary-value {
  display: block;
  margin-bottom: 8px;
  font-size: 1.6rem;
  line-height: 1;
  color: var(--rpms-text, #0f172a);
}

.admin-home__summary-hint {
  font-size: 12px;
  color: #64748b;
  line-height: 1.5;
}

.admin-home__charts {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 20px;
}

.admin-home__chart {
  min-height: 330px;
}

.admin-home__chart--wide {
  grid-column: 1 / -1;
}

.admin-home__chart-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 16px;
}

.admin-home__chart-title {
  margin: 0;
  font-size: 1rem;
  font-weight: 700;
  color: var(--rpms-text, #0f172a);
}

.admin-home__chart-subtitle {
  margin: 6px 0 0;
  color: var(--rpms-text-muted, #64748b);
  font-size: 13px;
}

.admin-home__line {
  width: 100%;
  height: 270px;
}

.admin-home__trend-label {
  letter-spacing: 0.02em;
  user-select: none;
}

.admin-home__bars {
  display: grid;
  grid-template-columns: repeat(6, minmax(0, 1fr));
  gap: 12px;
  height: 240px;
  align-items: end;
}

.admin-home__bar-item {
  display: flex;
  flex-direction: column;
  gap: 10px;
  height: 100%;
}

.admin-home__bar-top {
  font-size: 12px;
  color: var(--rpms-text-muted, #64748b);
}

.admin-home__bar-top strong {
  display: block;
  margin-top: 2px;
  color: var(--rpms-text, #0f172a);
}

.admin-home__bar-track {
  flex: 1;
  display: flex;
  align-items: end;
  min-height: 160px;
  padding: 6px;
  border-radius: 14px;
  background: linear-gradient(180deg, rgba(248, 250, 252, 0.95), rgba(241, 245, 249, 0.9));
  border: 1px solid rgba(226, 232, 240, 0.9);
}

.admin-home__bar-fill {
  width: 100%;
  min-height: 6px;
  border-radius: 12px 12px 6px 6px;
  box-shadow: 0 10px 24px rgba(42, 110, 187, 0.18);
}

.admin-home__pie-wrap,
.admin-home__donut-wrap {
  display: flex;
  align-items: center;
  gap: 18px;
}

.admin-home__pie,
.admin-home__donut {
  width: 180px;
  height: 180px;
  flex-shrink: 0;
  filter: drop-shadow(0 10px 22px rgba(15, 23, 42, 0.08));
}

.admin-home__legend,
.admin-home__ring-legend {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 10px;
  flex: 1;
}

.admin-home__legend li,
.admin-home__ring-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  font-size: 13px;
  color: var(--rpms-text, #0f172a);
  padding: 8px 10px;
  border-radius: 12px;
  background: #f8fafc;
  border: 1px solid rgba(226, 232, 240, 0.9);
}

.admin-home__legend li span,
.admin-home__ring-item span {
  flex: 1;
}

.admin-home__legend-dot {
  width: 10px;
  height: 10px;
  border-radius: 999px;
  flex-shrink: 0;
}

.admin-home__rank-list {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.admin-home__rank-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.admin-home__rank-meta {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 13px;
}

.admin-home__rank-index {
  width: 28px;
  height: 28px;
  border-radius: 10px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: rgba(42, 110, 187, 0.1);
  color: var(--rpms-primary, #2a6ebb);
  font-weight: 700;
}

.admin-home__rank-name {
  flex: 1;
  color: var(--rpms-text, #0f172a);
  font-weight: 600;
}

.admin-home__rank-value {
  color: var(--rpms-text-muted, #64748b);
}

.admin-home__rank-track {
  height: 14px;
  border-radius: 999px;
  background: #eef2f7;
  overflow: hidden;
}

.admin-home__rank-fill {
  height: 100%;
  border-radius: inherit;
}

@media (max-width: 1200px) {
  .admin-home__summary-grid {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }

  .admin-home__charts {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 700px) {
  .admin-home__hero-top,
  .admin-home__pie-wrap,
  .admin-home__donut-wrap {
    flex-direction: column;
    align-items: flex-start;
  }

  .admin-home__summary-grid,
  .admin-home__bars {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}
</style>
