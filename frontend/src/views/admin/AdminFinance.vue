<script setup>
import { onMounted, ref, watch } from 'vue'
import http from '@/api/http'
import RpmsPagination from '@/components/RpmsPagination.vue'
import { unwrapPaginated } from '@/utils/unwrapPaginated'
import { useToast } from '@/utils/toast'

const chargeItems = ref([])
const chargeTotal = ref(0)
const chargePage = ref(1)
const chargePageSize = ref(10)
const billPropertyOptions = ref([])
const billChargeOptions = ref([])

const bills = ref([])
const billsTotal = ref(0)
const billsPage = ref(1)
const billsPageSize = ref(10)

const msg = ref('')
const err = ref('')
const chargeFilter = ref({ search: '', type: '', is_active: '' })
const billFilter = ref({ year_month: '', status: '', owner: '', charge_item: '', search: '' })

const newCharge = ref({
  name: '',
  type: 'property_fee',
  unit_price: '',
  unit: '元/㎡',
  description: '',
  is_active: true,
})
const newBill = ref({
  property: '',
  charge_item: '',
  year_month: '',
  amount: '',
  status: 'unpaid',
  due_date: '',
  remark: '',
})
const importText = ref('')
const importFileTip = ref('')
const genBill = ref({ year_month: '', charge_item: '', due_date: '' })
const toast = useToast()

function nowYM() {
  const d = new Date()
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`
}

function defaultDueDate() {
  const d = new Date()
  d.setDate(d.getDate() + 30)
  return d.toISOString().slice(0, 10)
}

async function refreshCharges() {
  const params = { page: chargePage.value, page_size: chargePageSize.value }
  if (chargeFilter.value.search.trim()) params.search = chargeFilter.value.search.trim()
  if (chargeFilter.value.type) params.type = chargeFilter.value.type
  if (chargeFilter.value.is_active !== '') params.is_active = chargeFilter.value.is_active
  const { data } = await http.get('/api/finance/charge-items/', {
    params,
  })
  const u = unwrapPaginated(data)
  chargeItems.value = u.list
  chargeTotal.value = u.count
}

async function refreshBills() {
  const params = { page: billsPage.value, page_size: billsPageSize.value }
  if (billFilter.value.year_month.trim()) params.year_month = billFilter.value.year_month.trim()
  if (billFilter.value.status) params.status = billFilter.value.status
  if (billFilter.value.owner.trim()) params.owner = billFilter.value.owner.trim()
  if (billFilter.value.charge_item.trim()) params.charge_item = billFilter.value.charge_item.trim()
  if (billFilter.value.search.trim()) params.search = billFilter.value.search.trim()
  const { data } = await http.get('/api/finance/bills/', {
    params,
  })
  const u = unwrapPaginated(data)
  bills.value = u.list
  billsTotal.value = u.count
}

async function refresh() {
  await Promise.all([refreshCharges(), refreshBills()])
}

async function refreshBillFormOptions() {
  const [propsRes, chargeRes] = await Promise.all([
    http.get('/api/users/properties/', { params: { page: 1, page_size: 200, type: 'room' } }),
    http.get('/api/finance/charge-items/', { params: { page: 1, page_size: 200 } }),
  ])
  billPropertyOptions.value = unwrapPaginated(propsRes.data).list
  billChargeOptions.value = unwrapPaginated(chargeRes.data).list
  if (!newBill.value.year_month) newBill.value.year_month = nowYM()
  if (!newBill.value.due_date) newBill.value.due_date = defaultDueDate()
  if (!newBill.value.status) newBill.value.status = 'unpaid'
}

onMounted(async () => {
  await Promise.all([refresh(), refreshBillFormOptions()])
})

watch([chargePage, chargePageSize], refreshCharges)
watch([billsPage, billsPageSize], refreshBills)
watch(() => newBill.value.charge_item, (val) => {
  const selected = billChargeOptions.value.find((i) => String(i.id) === String(val))
  if (selected && (newBill.value.amount === '' || newBill.value.amount === null)) {
    newBill.value.amount = selected.unit_price
  }
})

async function createCharge() {
  err.value = ''
  try {
    await http.post('/api/finance/charge-items/', {
      ...newCharge.value,
      unit_price: Number(newCharge.value.unit_price),
    })
    newCharge.value = { name: '', type: 'property_fee', unit_price: '', unit: '元/㎡', description: '', is_active: true }
    msg.value = '收费项目已新增'
    toast.success('收费项目已新增')
    chargePage.value = 1
    await refreshCharges()
  } catch (e) {
    err.value = JSON.stringify(e.response?.data || e.message)
    toast.error(toast.errorMessage(e, '新增收费项目失败'))
  }
}

async function createBill() {
  err.value = ''
  try {
    await http.post('/api/finance/bills/', {
      property: newBill.value.property ? Number(newBill.value.property) : '',
      charge_item: newBill.value.charge_item ? Number(newBill.value.charge_item) : '',
      year_month: newBill.value.year_month,
      amount: newBill.value.amount === '' ? '' : Number(newBill.value.amount),
      status: newBill.value.status,
      due_date: newBill.value.due_date,
      remark: newBill.value.remark,
    })
    newBill.value = {
      property: '',
      charge_item: '',
      year_month: '',
      amount: '',
      status: 'unpaid',
      due_date: '',
      remark: '',
    }
    msg.value = '账单已新增'
    toast.success('账单已新增')
    billsPage.value = 1
    await refreshBills()
  } catch (e) {
    err.value = JSON.stringify(e.response?.data || e.message)
    toast.error(toast.errorMessage(e, '新增账单失败'))
  }
}

async function generateBills() {
  err.value = ''
  try {
    await http.post('/api/finance/bills/generate/', {
      year_month: genBill.value.year_month,
      charge_item: Number(genBill.value.charge_item),
      due_date: genBill.value.due_date || undefined,
    })
    msg.value = '账单已生成'
    toast.success('账单已生成')
    billsPage.value = 1
    await refreshBills()
  } catch (e) {
    err.value = JSON.stringify(e.response?.data || e.message)
    toast.error(toast.errorMessage(e, '生成账单失败'))
  }
}

function searchCharges() {
  chargePage.value = 1
  refreshCharges()
}

function resetCharges() {
  chargeFilter.value = { search: '', type: '', is_active: '' }
  chargePage.value = 1
  refreshCharges()
}

function searchBills() {
  billsPage.value = 1
  refreshBills()
}

function resetBills() {
  billFilter.value = { year_month: '', status: '', owner: '', charge_item: '', search: '' }
  billsPage.value = 1
  refreshBills()
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

async function importBills() {
  err.value = ''
  try {
    const rows = JSON.parse(importText.value || '[]')
    const { data } = await http.post('/api/finance/bills/batch_create/', { rows })
    msg.value = `账单导入完成：新增 ${data.created || 0} 条，失败 ${(data.errors || []).length} 条`
    toast.success(`账单导入完成：新增 ${data.created || 0} 条`)
    importText.value = ''
    importFileTip.value = ''
    billsPage.value = 1
    await refreshBills()
  } catch (e) {
    err.value = JSON.stringify(e.response?.data || e.message)
    toast.error(toast.errorMessage(e, '导入账单失败'))
  }
}
</script>

<template>
  <div>
    <p v-if="msg" class="rpms-msg--ok">{{ msg }}</p>
    <p v-if="err" class="rpms-msg--err">{{ err }}</p>
    <div class="rpms-panel">
      <h2 class="rpms-panel-title">收费项目 - 新增</h2>
      <div class="rpms-form-row">
        <input v-model="newCharge.name" class="rpms-input" placeholder="项目名称" />
        <select v-model="newCharge.type" class="rpms-select">
          <option value="property_fee">物业费</option>
          <option value="parking_fee">停车费</option>
          <option value="water_fee">水费</option>
          <option value="electricity_fee">电费</option>
          <option value="gas_fee">燃气费</option>
          <option value="other">其他</option>
        </select>
        <input v-model="newCharge.unit_price" class="rpms-input" placeholder="单价" />
        <input v-model="newCharge.unit" class="rpms-input" placeholder="单位" />
        <label class="rpms-muted" style="display: flex; align-items: center; gap: 6px">
          <input v-model="newCharge.is_active" type="checkbox" />
          启用
        </label>
      </div>
      <textarea
        v-model="newCharge.description"
        class="rpms-textarea"
        rows="2"
        placeholder="描述（可选）"
        style="width: 100%; box-sizing: border-box"
      />
      <button type="button" class="rpms-btn rpms-btn--primary" style="margin-top: 10px" @click="createCharge">
        新增收费项目
      </button>
    </div>
    <div class="rpms-panel">
      <h2 class="rpms-panel-title">收费项目 - 参数搜索</h2>
      <div class="rpms-form-row">
        <input v-model="chargeFilter.search" class="rpms-input" placeholder="项目名称关键词" />
        <select v-model="chargeFilter.type" class="rpms-select">
          <option value="">全部类型</option>
          <option value="property_fee">物业费</option>
          <option value="parking_fee">停车费</option>
          <option value="water_fee">水费</option>
          <option value="electricity_fee">电费</option>
          <option value="gas_fee">燃气费</option>
          <option value="other">其他</option>
        </select>
        <select v-model="chargeFilter.is_active" class="rpms-select">
          <option value="">全部状态</option>
          <option value="true">启用</option>
          <option value="false">停用</option>
        </select>
        <button type="button" class="rpms-btn rpms-btn--primary" @click="searchCharges">查询</button>
        <button type="button" class="rpms-btn rpms-btn--secondary" @click="resetCharges">重置</button>
      </div>
    </div>
    <div class="rpms-panel">
      <h2 class="rpms-panel-title">收费项目列表</h2>
      <div class="rpms-table-wrap">
        <table class="rpms-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>名称</th>
              <th>类型</th>
              <th>单价</th>
              <th>状态</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="i in chargeItems" :key="i.id">
              <td>{{ i.id }}</td>
              <td>{{ i.name }}</td>
              <td>{{ i.type }}</td>
              <td>{{ i.unit_price }}</td>
              <td>{{ i.is_active ? '启用' : '停用' }}</td>
            </tr>
          </tbody>
        </table>
      </div>
      <RpmsPagination
        :page="chargePage"
        :page-size="chargePageSize"
        :total="chargeTotal"
        @update:page="chargePage = $event"
        @update:page-size="chargePageSize = $event"
      />
    </div>
    <div class="rpms-panel">
      <h2 class="rpms-panel-title">新增账单</h2>
      <div class="rpms-form-row">
        <select v-model="newBill.property" class="rpms-select">
          <option value="">请选择房产</option>
          <option v-for="item in billPropertyOptions" :key="item.id" :value="item.id">
            {{ item.room_number || item.name || `房产 #${item.id}` }}
          </option>
        </select>
        <select v-model="newBill.charge_item" class="rpms-select">
          <option value="">请选择收费项目</option>
          <option v-for="item in billChargeOptions" :key="item.id" :value="item.id">
            {{ item.name }} / {{ item.unit_price }}
          </option>
        </select>
        <input v-model="newBill.year_month" class="rpms-input" placeholder="账期 2026-04" />
        <input v-model="newBill.amount" class="rpms-input" placeholder="金额" />
        <select v-model="newBill.status" class="rpms-select">
          <option value="unpaid">未缴费</option>
          <option value="paid">已缴费</option>
          <option value="overdue">已逾期</option>
        </select>
        <input v-model="newBill.due_date" class="rpms-input" placeholder="截止日期 YYYY-MM-DD" />
      </div>
      <textarea
        v-model="newBill.remark"
        class="rpms-textarea"
        rows="2"
        placeholder="备注（可选）"
        style="width: 100%; box-sizing: border-box"
      />
      <button type="button" class="rpms-btn rpms-btn--primary" style="margin-top: 10px" @click="createBill">
        新增账单
      </button>
    </div>
    <div class="rpms-panel">
      <h2 class="rpms-panel-title">批量导入账单（文件）</h2>
      <p class="rpms-muted">JSON格式：[{"property":1,"charge_item":1,"year_month":"2026-04","amount":"120.00","status":"unpaid","due_date":"2026-04-30","remark":"备注"}]，可直接选择json文件。</p>
      <textarea v-model="importText" class="rpms-textarea" rows="4" style="width: 100%; box-sizing: border-box" />
      <div class="rpms-form-row">
        <input type="file" accept=".json,application/json" @change="onImportFile" />
        <button type="button" class="rpms-btn rpms-btn--secondary" @click="importBills">批量导入账单</button>
      </div>
      <p v-if="importFileTip" class="rpms-muted">{{ importFileTip }}</p>
    </div>
    <div class="rpms-panel">
      <h2 class="rpms-panel-title">生成账单</h2>
      <div class="rpms-form-row">
        <input v-model="genBill.year_month" class="rpms-input" placeholder="账期 如 2026-04" />
        <input v-model="genBill.charge_item" class="rpms-input" placeholder="收费项目ID" />
        <input v-model="genBill.due_date" class="rpms-input" placeholder="截止日期 YYYY-MM-DD" />
        <button type="button" class="rpms-btn rpms-btn--primary" @click="generateBills">生成</button>
      </div>
      <p class="rpms-muted" style="margin-top: 8px">
        <a class="rpms-link" href="/api/finance/bills/export_csv/" target="_blank" rel="noreferrer"
          >导出账单 CSV</a
        >
      </p>
    </div>
    <div class="rpms-panel">
      <h2 class="rpms-panel-title">账单列表</h2>
      <div class="rpms-form-row">
        <input v-model="billFilter.year_month" class="rpms-input" placeholder="账期 YYYY-MM" />
        <select v-model="billFilter.status" class="rpms-select">
          <option value="">全部状态</option>
          <option value="unpaid">未缴费</option>
          <option value="paid">已缴费</option>
          <option value="overdue">已逾期</option>
        </select>
        <input v-model="billFilter.owner" class="rpms-input" placeholder="业主ID" />
        <input v-model="billFilter.charge_item" class="rpms-input" placeholder="收费项目ID" />
        <input v-model="billFilter.search" class="rpms-input" placeholder="房号/业主/收费项关键词" />
        <button type="button" class="rpms-btn rpms-btn--primary" @click="searchBills">查询</button>
        <button type="button" class="rpms-btn rpms-btn--secondary" @click="resetBills">重置</button>
      </div>
      <div class="rpms-table-wrap">
        <table class="rpms-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>房产</th>
              <th>收费项</th>
              <th>账期</th>
              <th>金额</th>
              <th>状态</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="b in bills" :key="b.id">
              <td>{{ b.id }}</td>
              <td>{{ b.property }}</td>
              <td>{{ b.charge_item_name }}</td>
              <td>{{ b.year_month }}</td>
              <td>{{ b.amount }}</td>
              <td>{{ b.status }}</td>
            </tr>
          </tbody>
        </table>
      </div>
      <RpmsPagination
        :page="billsPage"
        :page-size="billsPageSize"
        :total="billsTotal"
        @update:page="billsPage = $event"
        @update:page-size="billsPageSize = $event"
      />
    </div>
  </div>
</template>
