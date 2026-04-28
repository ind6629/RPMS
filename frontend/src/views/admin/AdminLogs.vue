<script setup>
import { onMounted, ref, watch } from 'vue'
import http from '@/api/http'
import RpmsPagination from '@/components/RpmsPagination.vue'
import { unwrapPaginated } from '@/utils/unwrapPaginated'
import { useToast } from '@/utils/toast'

const logs = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(10)
const msg = ref('')
const actionFilter = ref('')
const userFilter = ref('')
const newLog = ref({ action: '', detail: '' })
const toast = useToast()

async function refresh() {
  const params = { page: page.value, page_size: pageSize.value }
  if (actionFilter.value.trim()) params.action = actionFilter.value.trim()
  if (userFilter.value.trim()) params.user = userFilter.value.trim()
  const { data } = await http.get('/api/operation/logs/', {
    params,
  })
  const u = unwrapPaginated(data)
  logs.value = u.list
  total.value = u.count
}

onMounted(refresh)

watch([page, pageSize], refresh)

function search() {
  page.value = 1
  refresh()
}

function resetSearch() {
  actionFilter.value = ''
  userFilter.value = ''
  page.value = 1
  refresh()
}

async function addLog() {
  try {
    await http.post('/api/operation/logs/manual_add/', {
      action: newLog.value.action,
      detail: newLog.value.detail,
    })
    msg.value = '系统日志已新增'
    toast.success('系统日志已新增')
    newLog.value = { action: '', detail: '' }
    page.value = 1
    await refresh()
  } catch (e) {
    toast.error(toast.errorMessage(e, '新增系统日志失败'))
  }
}
</script>

<template>
  <div>
    <p v-if="msg" class="rpms-msg--ok">{{ msg }}</p>
    <div class="rpms-panel">
      <h2 class="rpms-panel-title">新增系统日志</h2>
      <div class="rpms-form-row">
        <input v-model="newLog.action" class="rpms-input" placeholder="操作类型，如 manual_check" />
      </div>
      <textarea
        v-model="newLog.detail"
        class="rpms-textarea"
        rows="3"
        placeholder="日志详情"
        style="width: 100%; box-sizing: border-box"
      />
      <button type="button" class="rpms-btn rpms-btn--primary" style="margin-top: 10px" @click="addLog">
        新增日志
      </button>
    </div>
    <div class="rpms-panel">
      <h2 class="rpms-panel-title">导出</h2>
      <a class="rpms-link" href="/api/operation/logs/export_csv/" target="_blank" rel="noreferrer"
        >下载日志 CSV</a
      >
    </div>
    <div class="rpms-panel">
      <h2 class="rpms-panel-title">系统日志</h2>
      <div class="rpms-form-row">
        <input v-model="actionFilter" class="rpms-input" placeholder="按操作类型筛选" />
        <input v-model="userFilter" class="rpms-input" placeholder="按用户ID筛选" />
        <button type="button" class="rpms-btn rpms-btn--primary" @click="search">查询</button>
        <button type="button" class="rpms-btn rpms-btn--secondary" @click="resetSearch">重置</button>
      </div>
      <div class="rpms-table-wrap">
        <table class="rpms-table">
          <thead>
            <tr>
              <th>时间</th>
              <th>用户</th>
              <th>操作</th>
              <th>详情</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="g in logs" :key="g.id">
              <td>{{ g.created_at }}</td>
              <td>{{ g.user_name }}</td>
              <td>{{ g.action }}</td>
              <td>{{ g.detail }}</td>
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
  </div>
</template>
