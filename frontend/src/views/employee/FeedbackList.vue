<script setup>
import { onMounted, ref, watch } from 'vue'
import http from '@/api/http'
import RpmsPagination from '@/components/RpmsPagination.vue'
import { unwrapPaginated } from '@/utils/unwrapPaginated'

const list = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(10)

async function load() {
  const { data } = await http.get('/api/property/feedback/', {
    params: { page: page.value, page_size: pageSize.value },
  })
  const u = unwrapPaginated(data)
  list.value = u.list
  total.value = u.count
}

onMounted(load)

watch([page, pageSize], load)
</script>

<template>
  <div>
    <div v-if="total > 0" class="rpms-panel">
      <h2 class="rpms-panel-title">反馈列表</h2>
      <div class="rpms-table-wrap">
        <table class="rpms-table">
          <thead>
            <tr>
              <th>工单</th>
              <th>评分</th>
              <th>评语</th>
              <th>时间</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="f in list" :key="f.id">
              <td>#{{ f.order }}</td>
              <td>{{ f.rating }}</td>
              <td>{{ f.comment }}</td>
              <td>{{ f.created_at?.slice(0, 16) }}</td>
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
    <p v-else class="rpms-muted">暂无反馈</p>
  </div>
</template>
