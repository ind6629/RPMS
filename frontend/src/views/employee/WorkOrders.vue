<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import http from '@/api/http'
import RpmsPagination from '@/components/RpmsPagination.vue'
import { formatDateCN, statusLabel } from '@/utils/display'
import { unwrapPaginated } from '@/utils/unwrapPaginated'
import { useToast } from '@/utils/toast'

const list = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(10)
const remark = ref({})
const loading = ref(false)
const error = ref('')
const toast = useToast()
const summary = ref({
  total: 0,
  pending: 0,
  processing: 0,
  completed: 0,
  feedback_total: 0,
})
const latestFeedback = ref([])

const cards = computed(() => [
  { label: '我的工单', value: summary.value.total, hint: '当前分配给我的全部工单' },
  { label: '待处理', value: summary.value.pending, hint: '需尽快响应' },
  { label: '处理中', value: summary.value.processing, hint: '正在跟进' },
  { label: '已完成', value: summary.value.completed, hint: '已办结工单' },
  { label: '服务反馈', value: summary.value.feedback_total, hint: '收到的业主评价' },
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

const statusSlices = computed(() => {
  const items = [
    { label: '待处理', value: summary.value.pending, color: '#2A6EBB' },
    { label: '处理中', value: summary.value.processing, color: '#EA580C' },
    { label: '已完成', value: summary.value.completed, color: '#16A34A' },
  ]
  const totalValue = items.reduce((s, i) => s + i.value, 0) || 1
  let start = -90
  return items.map((item) => {
    const sweep = (item.value / totalValue) * 360
    const end = start + sweep
    const path = item.value ? piePath(50, 50, 38, start, end) : ''
    start = end
    return { ...item, path }
  })
})

const feedbackBars = computed(() => [
  { label: '反馈总数', value: summary.value.feedback_total, color: '#7C3AED' },
  { label: '已完成工单', value: summary.value.completed, color: '#16A34A' },
])

const maxFeedback = computed(() => Math.max(...feedbackBars.value.map((i) => i.value), 1))

async function load() {
  loading.value = true
  error.value = ''
  try {
    const [totalRes, pendingRes, processingRes, completedRes, feedbackRes, ordersRes, feedbackListRes] =
      await Promise.all([
        http.get('/api/property/repairs/', { params: { page: 1, page_size: 1 } }),
        http.get('/api/property/repairs/', { params: { page: 1, page_size: 1, status: 'pending' } }),
        http.get('/api/property/repairs/', { params: { page: 1, page_size: 1, status: 'processing' } }),
        http.get('/api/property/repairs/', { params: { page: 1, page_size: 1, status: 'completed' } }),
        http.get('/api/property/feedback/', { params: { page: 1, page_size: 1 } }),
        http.get('/api/property/repairs/', { params: { page: page.value, page_size: pageSize.value } }),
        http.get('/api/property/feedback/', { params: { page: 1, page_size: 5 } }),
      ])

    const u = unwrapPaginated(ordersRes.data)
    list.value = u.list
    total.value = u.count
    summary.value = {
      total: totalRes.data?.count || 0,
      pending: pendingRes.data?.count || 0,
      processing: processingRes.data?.count || 0,
      completed: completedRes.data?.count || 0,
      feedback_total: feedbackRes.data?.count || 0,
    }
    latestFeedback.value = feedbackListRes.data?.results || []
  } catch (e) {
    error.value = e.response?.data?.detail || e.message || '加载失败'
  } finally {
    loading.value = false
  }
}

onMounted(load)

watch([page, pageSize], load)

async function complete(id) {
  try {
    await http.post(`/api/property/repairs/${id}/complete/`, {
      remark: remark.value[id] || '',
    })
    toast.success(`工单 #${id} 已办结`)
    await load()
  } catch (e) {
    toast.error(toast.errorMessage(e, '办结工单失败'))
  }
}
</script>

<template>
  <div class="role-dashboard">
    <div class="rpms-panel role-dashboard__hero">
      <div class="role-dashboard__hero-top">
        <div>
          <p class="role-dashboard__eyebrow">员工看板</p>
          <h2 class="role-dashboard__title">工作台</h2>
          <p class="role-dashboard__subtitle">这里先看待办和完成情况，再进入工单处理。</p>
        </div>
        <div class="role-dashboard__badge">员工简化看板</div>
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
        <h3 class="role-dashboard__panel-title">工单状态环形图</h3>
        <div class="role-dashboard__pie-wrap">
          <svg viewBox="0 0 100 100" class="role-dashboard__pie" aria-label="工单状态环形图">
            <g v-for="slice in statusSlices" :key="slice.label">
              <path v-if="slice.path" :d="slice.path" :fill="slice.color" />
            </g>
            <circle cx="50" cy="50" r="20" fill="#fff" />
            <text x="50" y="47" text-anchor="middle" fill="#0f172a" font-size="10" font-weight="700">
              {{ summary.pending }}
            </text>
            <text x="50" y="58" text-anchor="middle" fill="#64748b" font-size="8">待处理</text>
          </svg>
          <div class="role-dashboard__legend">
            <div v-for="item in statusSlices" :key="item.label" class="role-dashboard__legend-item">
              <span class="role-dashboard__dot" :style="{ background: item.color }" />
              <span>{{ item.label }}</span>
              <strong>{{ item.value }}</strong>
            </div>
          </div>
        </div>
      </section>

      <section class="rpms-panel role-dashboard__panel">
        <h3 class="role-dashboard__panel-title">反馈与完成情况条形图</h3>
        <div class="role-dashboard__bar-list">
          <div v-for="item in feedbackBars" :key="item.label" class="role-dashboard__bar-row">
            <div class="role-dashboard__bar-meta">
              <span>{{ item.label }}</span>
              <strong>{{ item.value }}</strong>
            </div>
            <div class="role-dashboard__bar-track">
              <div class="role-dashboard__bar-fill" :style="{ width: `${(item.value / maxFeedback) * 100}%`, background: item.color }" />
            </div>
          </div>
        </div>
      </section>

      <section class="rpms-panel role-dashboard__panel role-dashboard__panel--wide">
        <h3 class="role-dashboard__panel-title">最近反馈</h3>
        <div class="role-dashboard__lists">
          <div>
            <p class="role-dashboard__mini-title">最新工单</p>
            <ul class="role-dashboard__mini-list">
              <li v-for="o in list.slice(0, 5)" :key="o.id">
                <span>#{{ o.id }} · {{ statusLabel(o.status) }}</span>
                <strong>{{ formatDateCN(o.created_at) }}</strong>
              </li>
              <li v-if="!list.length" class="rpms-muted">暂无工单</li>
            </ul>
          </div>
          <div>
            <p class="role-dashboard__mini-title">反馈记录</p>
            <ul class="role-dashboard__mini-list">
              <li v-for="f in latestFeedback" :key="f.id">
                <span>#{{ f.order }} · {{ f.rating }}星</span>
                <strong>{{ formatDateCN(f.created_at) }}</strong>
              </li>
              <li v-if="!latestFeedback.length" class="rpms-muted">暂无反馈</li>
            </ul>
          </div>
        </div>
      </section>
    </div>

    <p class="rpms-muted" style="margin-bottom: 16px">
      新报修单由系统自动分配给当前负载较低的员工。
    </p>
    <div v-if="total > 0" class="rpms-panel">
      <h2 class="rpms-panel-title">工单列表</h2>
      <div class="rpms-table-wrap">
        <table class="rpms-table">
          <thead>
            <tr>
              <th>编号</th>
              <th>状态</th>
              <th>业主</th>
              <th>描述</th>
              <th>备注 / 办结</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="o in list" :key="o.id">
              <td>{{ o.id }}</td>
              <td>{{ statusLabel(o.status) }}</td>
              <td>{{ o.user_info?.username }}</td>
              <td>{{ o.description?.slice(0, 56) }}</td>
              <td>
                <div class="rpms-form-row" style="margin: 0">
                  <input v-model="remark[o.id]" class="rpms-input" placeholder="处理备注" style="width: 140px" />
                  <button
                    v-if="o.status !== 'completed'"
                    type="button"
                    class="rpms-btn rpms-btn--primary"
                    @click="complete(o.id)"
                  >
                    办结
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      <RpmsPagination
        :page="page"
        :page-size="pageSize"
        :total="total"
        @update:page="page = $event"
        @update:page-size="pageSize = $event"
      />
    </div>
    <p v-else class="rpms-muted">暂无工单</p>
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
  grid-template-columns: repeat(2, minmax(0, 1fr));
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
  grid-template-columns: repeat(2, minmax(0, 1fr));
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
