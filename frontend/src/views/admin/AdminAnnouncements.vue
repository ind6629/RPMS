<script setup>
import { onMounted, ref, watch } from 'vue'
import http from '@/api/http'
import RpmsPagination from '@/components/RpmsPagination.vue'
import { unwrapPaginated } from '@/utils/unwrapPaginated'
import { useToast } from '@/utils/toast'

const announcements = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(10)
const msg = ref('')
const typeFilter = ref('')
const publishFilter = ref('')
const keyword = ref('')
const toast = useToast()
const newAnn = ref({
  title: '',
  content: '',
  type: 'notice',
  is_published: true,
  publish_time: '',
})

async function refresh() {
  const params = { page: page.value, page_size: pageSize.value }
  if (typeFilter.value) params.type = typeFilter.value
  if (publishFilter.value !== '') params.is_published = publishFilter.value
  if (keyword.value.trim()) params.search = keyword.value.trim()
  const { data } = await http.get('/api/operation/announcements/', {
    params,
  })
  const u = unwrapPaginated(data)
  announcements.value = u.list
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
  publishFilter.value = ''
  keyword.value = ''
  page.value = 1
  refresh()
}

async function createAnnouncement() {
  const payload = { ...newAnn.value }
  if (!payload.publish_time) payload.publish_time = null
  try {
    await http.post('/api/operation/announcements/', payload)
    msg.value = '公告已保存'
    toast.success('公告已保存')
    page.value = 1
    await refresh()
  } catch (e) {
    toast.error(toast.errorMessage(e, '保存公告失败'))
  }
}
</script>

<template>
  <div>
    <p v-if="msg" class="rpms-msg--ok">{{ msg }}</p>
    <div class="rpms-panel">
      <h2 class="rpms-panel-title">发布新公告</h2>
      <div class="rpms-form-row">
        <input v-model="newAnn.title" class="rpms-input" placeholder="标题" />
        <select v-model="newAnn.type" class="rpms-select">
          <option value="notice">通知</option>
          <option value="activity">活动</option>
          <option value="urgent">紧急</option>
        </select>
        <label class="rpms-muted" style="display: flex; align-items: center; gap: 6px">
          <input v-model="newAnn.is_published" type="checkbox" />
          发布
        </label>
        <input v-model="newAnn.publish_time" class="rpms-input" type="datetime-local" />
      </div>
      <textarea
        v-model="newAnn.content"
        class="rpms-textarea"
        rows="4"
        placeholder="内容"
        style="width: 100%; box-sizing: border-box; margin-top: 8px"
      />
      <button type="button" class="rpms-btn rpms-btn--primary" style="margin-top: 10px" @click="createAnnouncement">
        保存公告
      </button>
    </div>
    <div class="rpms-panel">
      <h2 class="rpms-panel-title">公告列表</h2>
      <div class="rpms-form-row">
        <select v-model="typeFilter" class="rpms-select">
          <option value="">全部类型</option>
          <option value="notice">通知</option>
          <option value="activity">活动</option>
          <option value="urgent">紧急</option>
        </select>
        <select v-model="publishFilter" class="rpms-select">
          <option value="">全部发布状态</option>
          <option value="true">已发布</option>
          <option value="false">未发布</option>
        </select>
        <input v-model="keyword" class="rpms-input" placeholder="标题或内容关键词" />
        <button type="button" class="rpms-btn rpms-btn--primary" @click="onSearch">查询</button>
        <button type="button" class="rpms-btn rpms-btn--secondary" @click="resetSearch">重置</button>
      </div>
      <div class="rpms-table-wrap">
        <table class="rpms-table">
          <thead>
            <tr>
              <th>编号</th>
              <th>标题</th>
              <th>已发布</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="a in announcements" :key="a.id">
              <td>{{ a.id }}</td>
              <td>{{ a.title }}</td>
              <td>{{ a.is_published ? '是' : '否' }}</td>
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
