<script setup>
import { onMounted, ref, watch } from 'vue'
import http from '@/api/http'
import RpmsPagination from '@/components/RpmsPagination.vue'
import { formatDateTimeCN } from '@/utils/display'
import { unwrapPaginated } from '@/utils/unwrapPaginated'

const list = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(10)

async function load() {
  const { data } = await http.get('/api/operation/announcements/platform/', {
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
    <template v-if="total > 0">
      <article v-for="a in list" :key="a.id" class="rpms-announce">
        <h3>{{ a.title }}</h3>
        <p class="meta">{{ a.type }} · {{ formatDateTimeCN(a.publish_time || a.created_at) }}</p>
        <div class="body">{{ a.content }}</div>
      </article>
      <RpmsPagination
        :page="page"
        :page-size="pageSize"
        :total="total"
        @update:page="page = $event"
        @update:page-size="pageSize = $event"
      />
    </template>
    <p v-else class="rpms-muted">暂无公告</p>
  </div>
</template>
