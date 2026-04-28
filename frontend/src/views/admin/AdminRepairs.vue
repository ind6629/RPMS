<script setup>
import { onMounted, ref, watch } from 'vue'
import http from '@/api/http'
import RpmsPagination from '@/components/RpmsPagination.vue'
import { unwrapPaginated } from '@/utils/unwrapPaginated'
import { useToast } from '@/utils/toast'

const repairs = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(10)
const msg = ref('')
const statusFilter = ref('')
const userFilter = ref('')
const assignedFilter = ref('')
const propertyFilter = ref('')
const keyword = ref('')

const newOrder = ref({
  property: '',
  user: '',
  description: '',
  status: 'pending',
  assigned_to: '',
})
const importText = ref('')
const importFileTip = ref('')
const toast = useToast()

async function refresh() {
  const params = { page: page.value, page_size: pageSize.value }
  if (statusFilter.value) params.status = statusFilter.value
  if (userFilter.value.trim()) params.user = userFilter.value.trim()
  if (assignedFilter.value.trim()) params.assigned_to = assignedFilter.value.trim()
  if (propertyFilter.value.trim()) params.property = propertyFilter.value.trim()
  if (keyword.value.trim()) params.search = keyword.value.trim()
  const { data } = await http.get('/api/property/repairs/', {
    params,
  })
  const u = unwrapPaginated(data)
  repairs.value = u.list
  total.value = u.count
}

onMounted(refresh)

watch([page, pageSize], refresh)

function search() {
  page.value = 1
  refresh()
}

function resetSearch() {
  statusFilter.value = ''
  userFilter.value = ''
  assignedFilter.value = ''
  propertyFilter.value = ''
  keyword.value = ''
  page.value = 1
  refresh()
}

async function createOne() {
  try {
    await http.post('/api/property/repairs/batch_create/', {
      rows: [
        {
          property: Number(newOrder.value.property),
          user: Number(newOrder.value.user),
          description: newOrder.value.description,
          status: newOrder.value.status,
          assigned_to: newOrder.value.assigned_to ? Number(newOrder.value.assigned_to) : null,
        },
      ],
    })
    msg.value = '工单已新增'
    toast.success('工单已新增')
    newOrder.value = { property: '', user: '', description: '', status: 'pending', assigned_to: '' }
    page.value = 1
    await refresh()
  } catch (e) {
    toast.error(toast.errorMessage(e, '新增工单失败'))
  }
}

function onImportFile(e) {
  const file = e.target.files?.[0]
  importFileTip.value = ''
  if (!file) return
  const reader = new FileReader()
  reader.onload = () => {
    importText.value = String(reader.result || '')
    importFileTip.value = `已载入文件：${file.name}`
  }
  reader.readAsText(file, 'utf-8')
  e.target.value = ''
}

async function importBatch() {
  try {
    const rows = JSON.parse(importText.value || '[]')
    const { data } = await http.post('/api/property/repairs/batch_create/', { rows })
    msg.value = `导入完成：新增 ${data.created || 0} 条，失败 ${(data.errors || []).length} 条`
    toast.success(`导入完成：新增 ${data.created || 0} 条`)
    importText.value = ''
    importFileTip.value = ''
    page.value = 1
    await refresh()
  } catch (e) {
    toast.error(toast.errorMessage(e, '导入工单失败'))
  }
}
</script>

<template>
  <div>
    <p v-if="msg" class="rpms-msg--ok">{{ msg }}</p>
    <div class="rpms-panel">
      <h2 class="rpms-panel-title">新增工单</h2>
      <div class="rpms-form-row">
        <input v-model="newOrder.property" class="rpms-input" placeholder="房产ID" />
        <input v-model="newOrder.user" class="rpms-input" placeholder="报修业主ID" />
        <select v-model="newOrder.status" class="rpms-select">
          <option value="pending">待处理</option>
          <option value="processing">处理中</option>
          <option value="completed">已完成</option>
          <option value="cancelled">已取消</option>
        </select>
        <input v-model="newOrder.assigned_to" class="rpms-input" placeholder="处理员工ID(可空)" />
      </div>
      <div class="rpms-field">
        <label>故障描述</label>
        <textarea v-model="newOrder.description" class="rpms-textarea" rows="3" />
      </div>
      <button type="button" class="rpms-btn rpms-btn--primary" @click="createOne">新增工单</button>
    </div>
    <div class="rpms-panel">
      <h2 class="rpms-panel-title">导入工单（JSON 文件或粘贴）</h2>
      <p class="rpms-muted">格式：[{"property":1,"user":2,"description":"描述","status":"processing","assigned_to":3}]</p>
      <textarea v-model="importText" class="rpms-textarea" rows="4" style="width: 100%" />
      <div class="rpms-form-row">
        <input type="file" accept=".json,application/json" @change="onImportFile" />
        <button type="button" class="rpms-btn rpms-btn--secondary" @click="importBatch">批量导入</button>
      </div>
      <p v-if="importFileTip" class="rpms-muted">{{ importFileTip }}</p>
    </div>
    <div class="rpms-panel">
      <h2 class="rpms-panel-title">导出</h2>
      <a class="rpms-link" href="/api/property/repairs/export_csv/" target="_blank" rel="noreferrer"
        >下载工单 CSV</a
      >
    </div>
    <div class="rpms-panel">
      <h2 class="rpms-panel-title">工单列表</h2>
      <div class="rpms-form-row">
        <select v-model="statusFilter" class="rpms-select">
          <option value="">全部状态</option>
          <option value="pending">待处理</option>
          <option value="processing">处理中</option>
          <option value="completed">已完成</option>
          <option value="cancelled">已取消</option>
        </select>
        <input v-model="userFilter" class="rpms-input" placeholder="报修人ID" />
        <input v-model="assignedFilter" class="rpms-input" placeholder="处理人ID" />
        <input v-model="propertyFilter" class="rpms-input" placeholder="房产ID" />
        <input v-model="keyword" class="rpms-input" placeholder="关键词(描述/用户名/房号)" />
        <button type="button" class="rpms-btn rpms-btn--primary" @click="search">查询</button>
        <button type="button" class="rpms-btn rpms-btn--secondary" @click="resetSearch">重置</button>
      </div>
      <div class="rpms-table-wrap">
        <table class="rpms-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>状态</th>
              <th>报修人</th>
              <th>处理人</th>
              <th>描述</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="o in repairs" :key="o.id">
              <td>{{ o.id }}</td>
              <td>{{ o.status }}</td>
              <td>{{ o.user_info?.username }}</td>
              <td>{{ o.assigned_to_info?.username }}</td>
              <td>{{ o.description?.slice(0, 48) }}</td>
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
