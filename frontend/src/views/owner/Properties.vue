<script setup>
import { onMounted, ref, watch } from 'vue'
import http from '@/api/http'
import RpmsPagination from '@/components/RpmsPagination.vue'
import { unwrapPaginated } from '@/utils/unwrapPaginated'

const list = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(10)
const err = ref('')

async function load() {
  try {
    const { data } = await http.get('/api/users/properties/my_properties/', {
      params: { page: page.value, page_size: pageSize.value },
    })
    const u = unwrapPaginated(data)
    list.value = u.list
    total.value = u.count
    err.value = ''
  } catch {
    err.value = '加载失败'
  }
}

onMounted(load)

watch([page, pageSize], load)
</script>

<template>
  <div>
    <p v-if="err" class="rpms-msg--err">{{ err }}</p>
    <div v-if="total > 0" class="rpms-panel">
      <h2 class="rpms-panel-title">已绑定房屋</h2>
      <div class="rpms-table-wrap">
        <table class="rpms-table">
          <thead>
            <tr>
              <th>楼栋</th>
              <th>单元</th>
              <th>房号</th>
              <th>面积(㎡)</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="p in list" :key="p.id">
              <td>{{ p.building_number }}</td>
              <td>{{ p.unit_number }}</td>
              <td>{{ p.room_number }}</td>
              <td>{{ p.area }}</td>
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
    <p v-else-if="!err" class="rpms-muted">暂无绑定房产，请联系管理员在后台为您绑定。</p>
  </div>
</template>
