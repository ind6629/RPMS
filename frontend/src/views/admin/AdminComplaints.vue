<script setup>
import { onMounted, ref, watch } from 'vue'
import http from '@/api/http'
import RpmsPagination from '@/components/RpmsPagination.vue'
import { unwrapPaginated } from '@/utils/unwrapPaginated'
import { useToast } from '@/utils/toast'

const complaints = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(10)
const msg = ref('')
const typeFilter = ref('')
const statusFilter = ref('')
const userFilter = ref('')
const keyword = ref('')
const newComplaint = ref({
  user: '',
  type: 'service',
  title: '',
  description: '',
})
const toast = useToast()

async function refresh() {
  const params = { page: page.value, page_size: pageSize.value }
  if (typeFilter.value) params.type = typeFilter.value
  if (statusFilter.value) params.status = statusFilter.value
  if (userFilter.value.trim()) params.user = userFilter.value.trim()
  if (keyword.value.trim()) params.search = keyword.value.trim()
  const { data } = await http.get('/api/property/complaints/', {
    params,
  })
  const u = unwrapPaginated(data)
  complaints.value = u.list.map((x) => ({
    ...x,
    _st: x.status,
    _rm: x.handler_remark || '',
  }))
  total.value = u.count
}

onMounted(refresh)

watch([page, pageSize], refresh)

function onSearch() {
  page.value = 1
  refresh()
}

function resetSearch() {
  typeFilter.value = ''
  statusFilter.value = ''
  userFilter.value = ''
  keyword.value = ''
  page.value = 1
  refresh()
}

async function createComplaint() {
  try {
    await http.post('/api/property/complaints/', {
      user: Number(newComplaint.value.user),
      type: newComplaint.value.type,
      title: newComplaint.value.title,
      description: newComplaint.value.description,
      images: [],
    })
    msg.value = '投诉已新增'
    toast.success('投诉已新增')
    newComplaint.value = { user: '', type: 'service', title: '', description: '' }
    page.value = 1
    await refresh()
  } catch (e) {
    toast.error(toast.errorMessage(e, '新增投诉失败'))
  }
}

async function saveComplaint(c) {
  try {
    await http.patch(`/api/property/complaints/${c.id}/`, {
      status: c._st || c.status,
      handler_remark: c._rm ?? c.handler_remark ?? '',
    })
    msg.value = '已更新'
    toast.success('投诉已更新')
    await refresh()
  } catch (e) {
    toast.error(toast.errorMessage(e, '更新投诉失败'))
  }
}
</script>

<template>
  <div>
    <p v-if="msg" class="rpms-msg--ok">{{ msg }}</p>
    <div class="rpms-panel">
      <h2 class="rpms-panel-title">新增投诉建议</h2>
      <div class="rpms-form-row">
        <input v-model="newComplaint.user" class="rpms-input" placeholder="业主用户ID" />
        <select v-model="newComplaint.type" class="rpms-select">
          <option value="service">物业服务</option>
          <option value="environment">环境卫生</option>
          <option value="security">安全管理</option>
          <option value="facility">设施设备</option>
          <option value="other">其他</option>
        </select>
        <input v-model="newComplaint.title" class="rpms-input" placeholder="标题" />
      </div>
      <textarea
        v-model="newComplaint.description"
        class="rpms-textarea"
        rows="3"
        placeholder="问题描述"
        style="width: 100%; box-sizing: border-box"
      />
      <button type="button" class="rpms-btn rpms-btn--primary" style="margin-top: 10px" @click="createComplaint">
        新增投诉
      </button>
    </div>
    <div class="rpms-panel">
      <h2 class="rpms-panel-title">投诉与建议</h2>
      <div class="rpms-form-row">
        <select v-model="typeFilter" class="rpms-select">
          <option value="">全部类型</option>
          <option value="service">物业服务</option>
          <option value="environment">环境卫生</option>
          <option value="security">安全管理</option>
          <option value="facility">设施设备</option>
          <option value="other">其他</option>
        </select>
        <select v-model="statusFilter" class="rpms-select">
          <option value="">全部状态</option>
          <option value="pending">待处理</option>
          <option value="processing">处理中</option>
          <option value="completed">已完成</option>
        </select>
        <input v-model="userFilter" class="rpms-input" placeholder="业主用户ID" />
        <input v-model="keyword" class="rpms-input" placeholder="标题或描述关键词" />
        <button type="button" class="rpms-btn rpms-btn--primary" @click="onSearch">查询</button>
        <button type="button" class="rpms-btn rpms-btn--secondary" @click="resetSearch">重置</button>
      </div>
      <div class="rpms-table-wrap">
        <table class="rpms-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>标题</th>
              <th>状态</th>
              <th>处理</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="c in complaints" :key="c.id">
              <td>{{ c.id }}</td>
              <td>{{ c.title }}</td>
              <td>
                <select v-model="c._st" class="rpms-select">
                  <option value="pending">待处理</option>
                  <option value="processing">处理中</option>
                  <option value="completed">已完成</option>
                </select>
              </td>
              <td>
                <div class="rpms-form-row" style="margin: 0">
                  <input v-model="c._rm" class="rpms-input" placeholder="备注" />
                  <button type="button" class="rpms-btn rpms-btn--secondary" @click="saveComplaint(c)">
                    保存
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
  </div>
</template>
