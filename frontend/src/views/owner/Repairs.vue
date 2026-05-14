<script setup>
import { onMounted, ref, watch } from 'vue'
import http from '@/api/http'
import RpmsPagination from '@/components/RpmsPagination.vue'
import { formatDateTimeCN, statusLabel } from '@/utils/display'
import { unwrapPaginated } from '@/utils/unwrapPaginated'
import { useToast } from '@/utils/toast'

const props = ref([])
const orders = ref([])
const ordersTotal = ref(0)
const orderPage = ref(1)
const orderPageSize = ref(10)

const completedOrders = ref([])

const propertyId = ref('')
const description = ref('')
const imageUrls = ref('')
const err = ref('')
const msg = ref('')
const toast = useToast()

const fbOrder = ref('')
const rating = ref(5)
const comment = ref('')
const fbMsg = ref('')

async function loadMyPropertiesForSelect() {
  const { data } = await http.get('/api/users/properties/my_properties/', {
    params: { page: 1, page_size: 100 },
  })
  const u = unwrapPaginated(data)
  props.value = u.list
}

async function loadCompletedForFeedback() {
  const { data } = await http.get('/api/property/repairs/', {
    params: { status: 'completed', page: 1, page_size: 100 },
  })
  const u = unwrapPaginated(data)
  completedOrders.value = u.list
}

async function loadOrders() {
  const { data } = await http.get('/api/property/repairs/', {
    params: { page: orderPage.value, page_size: orderPageSize.value },
  })
  const u = unwrapPaginated(data)
  orders.value = u.list
  ordersTotal.value = u.count
}

async function load() {
  await Promise.all([loadMyPropertiesForSelect(), loadOrders(), loadCompletedForFeedback()])
}

onMounted(load)

watch([orderPage, orderPageSize], () => {
  loadOrders()
})

function parseImages() {
  const s = imageUrls.value.trim()
  if (!s) return []
  return s.split(/[\n,]/).map((x) => x.trim()).filter(Boolean)
}

async function submit() {
  err.value = ''
  msg.value = ''
  try {
    await http.post('/api/property/repairs/', {
      property: Number(propertyId.value),
      description: description.value,
      images: parseImages(),
    })
    msg.value = '提交成功'
    toast.success('报修单已提交')
    description.value = ''
    imageUrls.value = ''
    orderPage.value = 1
    await load()
  } catch (e) {
    err.value = JSON.stringify(e.response?.data || e.message)
    toast.error(toast.errorMessage(e, '提交报修失败'))
  }
}

async function submitFeedback() {
  fbMsg.value = ''
  try {
    await http.post('/api/property/feedback/', {
      order: Number(fbOrder.value),
      rating: Number(rating.value),
      comment: comment.value,
    })
    fbMsg.value = '感谢您的评价'
    toast.success('反馈已提交')
    comment.value = ''
    await loadCompletedForFeedback()
  } catch (e) {
    fbMsg.value = JSON.stringify(e.response?.data || e.message)
    toast.error(toast.errorMessage(e, '提交反馈失败'))
  }
}
</script>

<template>
  <div>
    <div class="rpms-panel">
      <h2 class="rpms-panel-title">新建报修单</h2>
      <div class="rpms-field">
        <label>房产</label>
        <select v-model="propertyId" class="rpms-select" style="max-width: 400px">
          <option value="" disabled>请选择</option>
          <option v-for="p in props" :key="p.id" :value="p.id">
            {{ p.building_number }}栋 {{ p.unit_number }}单元 {{ p.room_number }}
          </option>
        </select>
      </div>
      <div class="rpms-field">
        <label>故障描述</label>
        <textarea v-model="description" class="rpms-textarea" rows="4" style="max-width: 640px" />
      </div>
      <div class="rpms-field">
        <label>图片地址（逗号或换行分隔，可选）</label>
        <textarea v-model="imageUrls" class="rpms-textarea" rows="2" style="max-width: 640px" />
      </div>
      <button type="button" class="rpms-btn rpms-btn--primary" @click="submit">提交报修</button>
      <p v-if="err" class="rpms-msg--err" style="margin-top: 12px">{{ err }}</p>
      <p v-if="msg" class="rpms-msg--ok" style="margin-top: 12px">{{ msg }}</p>
    </div>

    <div class="rpms-panel">
      <h2 class="rpms-panel-title">我的工单</h2>
      <div v-if="ordersTotal > 0" class="rpms-table-wrap">
        <table class="rpms-table">
          <thead>
            <tr>
              <th>编号</th>
              <th>状态</th>
              <th>时间</th>
              <th>描述</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="o in orders" :key="o.id">
              <td>{{ o.id }}</td>
              <td>{{ statusLabel(o.status) }}</td>
              <td>{{ formatDateTimeCN(o.created_at) }}</td>
              <td>{{ o.description?.slice(0, 40) }}</td>
            </tr>
          </tbody>
        </table>
      </div>
      <p v-else class="rpms-muted">暂无工单</p>
      <RpmsPagination
        :page="orderPage"
        :page-size="orderPageSize"
        :total="ordersTotal"
        @update:page="orderPage = $event"
        @update:page-size="orderPageSize = $event"
      />
    </div>

    <div class="rpms-panel">
      <h2 class="rpms-panel-title">服务反馈（已完成工单）</h2>
      <div class="rpms-field">
        <label>选择工单</label>
        <select v-model="fbOrder" class="rpms-select" style="max-width: 280px">
          <option value="" disabled>请选择</option>
          <option v-for="o in completedOrders" :key="o.id" :value="o.id">#{{ o.id }}</option>
        </select>
      </div>
      <div class="rpms-field">
        <label>评分 1–5</label>
        <input v-model.number="rating" class="rpms-input" type="number" min="1" max="5" style="max-width: 120px" />
      </div>
      <div class="rpms-field">
        <label>评语</label>
        <textarea v-model="comment" class="rpms-textarea" rows="2" style="max-width: 480px" />
      </div>
      <button type="button" class="rpms-btn rpms-btn--secondary" @click="submitFeedback">提交反馈</button>
      <p v-if="fbMsg" class="rpms-muted" style="margin-top: 10px">{{ fbMsg }}</p>
    </div>
  </div>
</template>
