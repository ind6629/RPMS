<script setup>
import { onMounted, ref, watch } from 'vue'
import http from '@/api/http'
import RpmsPagination from '@/components/RpmsPagination.vue'
import { unwrapPaginated } from '@/utils/unwrapPaginated'
import { useToast } from '@/utils/toast'

const users = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(10)
const msg = ref('')
const roleFilter = ref('')
const statusFilter = ref('')
const keyword = ref('')
const newUser = ref({ username: '', password: '', email: '', role: 'owner', phone: '' })
const toast = useToast()

async function refresh() {
  const params = { page: page.value, page_size: pageSize.value }
  if (roleFilter.value) params.role = roleFilter.value
  if (statusFilter.value) params.status = statusFilter.value
  if (keyword.value.trim()) params.search = keyword.value.trim()
  const { data } = await http.get('/api/users/accounts/', {
    params,
  })
  const u = unwrapPaginated(data)
  users.value = u.list
  total.value = u.count
}

onMounted(refresh)

watch([page, pageSize], refresh)

function onSearch() {
  page.value = 1
  refresh()
}

function resetSearch() {
  roleFilter.value = ''
  statusFilter.value = ''
  keyword.value = ''
  page.value = 1
  refresh()
}

async function createUser() {
  try {
    await http.post('/api/users/accounts/', { ...newUser.value })
    msg.value = '用户已创建'
    toast.success('用户已创建')
    page.value = 1
    await refresh()
  } catch (e) {
    toast.error(toast.errorMessage(e, '创建用户失败'))
  }
}

async function toggleUser(u) {
  try {
    await http.post(`/api/users/accounts/${u.id}/toggle-status/`)
    toast.success(`已${u.status ? '禁用' : '启用'}用户 ${u.username}`)
    await refresh()
  } catch (e) {
    toast.error(toast.errorMessage(e, '启用/禁用失败'))
  }
}
</script>

<template>
  <div>
    <p v-if="msg" class="rpms-msg--ok">{{ msg }}</p>
    <div class="rpms-panel">
      <h2 class="rpms-panel-title">新增用户</h2>
      <div class="rpms-form-row">
        <input v-model="newUser.username" class="rpms-input" placeholder="用户名" />
        <input v-model="newUser.password" class="rpms-input" type="password" placeholder="密码" />
        <input v-model="newUser.email" class="rpms-input" placeholder="邮箱" />
        <input v-model="newUser.phone" class="rpms-input" placeholder="手机" />
        <select v-model="newUser.role" class="rpms-select">
          <option value="owner">业主</option>
          <option value="employee">员工</option>
          <option value="admin">管理员</option>
        </select>
        <button type="button" class="rpms-btn rpms-btn--primary" @click="createUser">新增</button>
      </div>
    </div>
    <div class="rpms-panel">
      <h2 class="rpms-panel-title">用户列表</h2>
      <div class="rpms-form-row">
        <select v-model="roleFilter" class="rpms-select">
          <option value="">全部角色</option>
          <option value="owner">业主</option>
          <option value="employee">员工</option>
          <option value="admin">管理员</option>
        </select>
        <select v-model="statusFilter" class="rpms-select">
          <option value="">全部状态</option>
          <option value="true">启用</option>
          <option value="false">禁用</option>
        </select>
        <input v-model="keyword" class="rpms-input" placeholder="用户名/手机/邮箱" />
        <button type="button" class="rpms-btn rpms-btn--primary" @click="onSearch">查询</button>
        <button type="button" class="rpms-btn rpms-btn--secondary" @click="resetSearch">重置</button>
      </div>
      <div class="rpms-table-wrap">
        <table class="rpms-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>用户名</th>
              <th>角色</th>
              <th>状态</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="u in users" :key="u.id">
              <td>{{ u.id }}</td>
              <td>{{ u.username }}</td>
              <td>{{ u.role }}</td>
              <td>{{ u.status ? '启用' : '禁用' }}</td>
              <td>
                <button type="button" class="rpms-btn rpms-btn--secondary" @click="toggleUser(u)">
                  启用/禁用
                </button>
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
