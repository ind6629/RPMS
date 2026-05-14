<script setup>
import { onMounted, ref, watch } from 'vue'
import http from '@/api/http'
import RpmsPagination from '@/components/RpmsPagination.vue'
import { formatDateCN, statusLabel } from '@/utils/display'
import { unwrapPaginated } from '@/utils/unwrapPaginated'
import { useToast } from '@/utils/toast'

const list = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(10)
const err = ref('')
const toast = useToast()

async function load() {
  try {
    const { data } = await http.get('/api/finance/bills/', {
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

async function pay(id) {
  try {
    const { data } = await http.post(`/api/finance/bills/${id}/pay/`, { payment_method: 'alipay' })
    if (data?.pay_url) {
      toast.info('已跳转支付宝收银台')
      window.location.href = data.pay_url
      return
    }
    toast.error('未获取到支付宝支付链接')
  } catch (e) {
    toast.error(toast.errorMessage(e, '支付失败'))
  }
}
</script>

<template>
  <div>
    <p v-if="err" class="rpms-msg--err">{{ err }}</p>
    <div v-if="total > 0" class="rpms-panel">
      <h2 class="rpms-panel-title">账单列表</h2>
      <div class="rpms-table-wrap">
        <table class="rpms-table">
          <thead>
            <tr>
              <th>账期</th>
              <th>项目</th>
              <th>金额</th>
              <th>状态</th>
              <th>截止</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="b in list" :key="b.id">
              <td>{{ b.year_month }}</td>
              <td>{{ b.charge_item_name }}</td>
              <td>{{ b.amount }}</td>
              <td>{{ statusLabel(b.status) }}</td>
              <td>{{ formatDateCN(b.due_date) }}</td>
              <td>
                <button
                  v-if="b.status !== 'paid'"
                  type="button"
                  class="rpms-btn rpms-btn--primary"
                  @click="pay(b.id)"
                >
                  支付宝缴纳
                </button>
                <span v-else class="rpms-muted">{{ statusLabel(b.status) }}</span>
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
    <p v-else-if="!err" class="rpms-muted">暂无账单</p>
  </div>
</template>
