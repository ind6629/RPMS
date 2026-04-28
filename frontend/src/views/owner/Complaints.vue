<script setup>
import { onMounted, ref, watch } from 'vue'
import http from '@/api/http'
import RpmsPagination from '@/components/RpmsPagination.vue'
import { unwrapPaginated } from '@/utils/unwrapPaginated'
import { useToast } from '@/utils/toast'

const list = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(10)
const type = ref('service')
const title = ref('')
const description = ref('')
const images = ref('')
const err = ref('')
const msg = ref('')
const toast = useToast()

async function load() {
  const { data } = await http.get('/api/property/complaints/', {
    params: { page: page.value, page_size: pageSize.value },
  })
  const u = unwrapPaginated(data)
  list.value = u.list
  total.value = u.count
}

onMounted(load)

watch([page, pageSize], load)

function parseImages() {
  const s = images.value.trim()
  if (!s) return []
  return s.split(/[\n,]/).map((x) => x.trim()).filter(Boolean)
}

async function submit() {
  err.value = ''
  msg.value = ''
  try {
    await http.post('/api/property/complaints/', {
      type: type.value,
      title: title.value,
      description: description.value,
      images: parseImages(),
    })
    msg.value = '已提交'
    toast.success('投诉已提交')
    title.value = ''
    description.value = ''
    images.value = ''
    page.value = 1
    await load()
  } catch (e) {
    err.value = JSON.stringify(e.response?.data || e.message)
    toast.error(toast.errorMessage(e, '提交投诉失败'))
  }
}
</script>

<template>
  <div>
    <div class="rpms-panel">
      <h2 class="rpms-panel-title">提交投诉或建议</h2>
      <div class="rpms-field">
        <label>类型</label>
        <select v-model="type" class="rpms-select" style="max-width: 280px">
          <option value="service">物业服务</option>
          <option value="environment">环境卫生</option>
          <option value="security">安全管理</option>
          <option value="facility">设施设备</option>
          <option value="other">其他</option>
        </select>
      </div>
      <div class="rpms-field">
        <label>标题</label>
        <input v-model="title" class="rpms-input" style="max-width: 480px" />
      </div>
      <div class="rpms-field">
        <label>描述</label>
        <textarea v-model="description" class="rpms-textarea" rows="4" style="max-width: 640px" />
      </div>
      <div class="rpms-field">
        <label>证据图片地址（可选，逗号或换行分隔）</label>
        <textarea v-model="images" class="rpms-textarea" rows="2" style="max-width: 640px" />
      </div>
      <button type="button" class="rpms-btn rpms-btn--primary" @click="submit">提交</button>
      <p v-if="err" class="rpms-msg--err" style="margin-top: 12px">{{ err }}</p>
      <p v-if="msg" class="rpms-msg--ok" style="margin-top: 12px">{{ msg }}</p>
    </div>

    <div class="rpms-panel">
      <h2 class="rpms-panel-title">我的记录</h2>
      <div v-if="total > 0" class="rpms-table-wrap">
        <table class="rpms-table">
          <thead>
            <tr>
              <th>标题</th>
              <th>状态</th>
              <th>时间</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="c in list" :key="c.id">
              <td>{{ c.title }}</td>
              <td>{{ c.status }}</td>
              <td>{{ c.created_at?.slice(0, 16) }}</td>
            </tr>
          </tbody>
        </table>
      </div>
      <p v-else class="rpms-muted">暂无记录</p>
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
