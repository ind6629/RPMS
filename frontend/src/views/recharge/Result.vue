<script setup>
import { onBeforeUnmount, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import http from '@/api/http'
import { paymentMethodLabel } from '@/utils/display'
import { useToast } from '@/utils/toast'

const router = useRouter()
const toast = useToast()

const loading = ref(true)
const status = ref('pending')
const title = ref('正在确认支付宝支付结果')
const detail = ref('请稍候，系统正在核对支付宝回跳参数。')
const bill = ref(null)
const payment = ref(null)
const tradeNo = ref('')
const outTradeNo = ref('')
const pollTimer = ref(null)
const pollCount = ref(0)
const maxPollCount = 24

function queryParamsToObject() {
  const params = new URLSearchParams(window.location.search)
  const data = {}
  for (const [key, value] of params.entries()) {
    data[key] = value
  }
  return data
}

async function confirmPayment() {
  const params = queryParamsToObject()
  outTradeNo.value = params.out_trade_no || ''
  tradeNo.value = params.trade_no || ''

  if (!params.out_trade_no) {
    status.value = 'error'
    title.value = '支付结果缺少订单号'
    detail.value = '未收到支付宝回跳参数，请返回账单页重新查看。'
    toast.error(detail.value)
    loading.value = false
    return
  }

  try {
    const { data } = await http.post('/api/finance/bills/alipay/confirm/', params)
    if (data?.status === 'pending') {
      status.value = 'pending'
      title.value = '支付处理中'
      detail.value = data.detail || '支付宝交易尚未完成，请稍候自动刷新。'
      return false
    }

    status.value = 'success'
    title.value = '支付宝支付成功'
    detail.value = data.message || '账单已确认缴费。'
    bill.value = data.bill || null
    payment.value = data.payment || null
    tradeNo.value = data.trade_no || tradeNo.value
    outTradeNo.value = data.out_trade_no || outTradeNo.value
    toast.success('支付宝支付已确认')
    if (pollTimer.value) {
      clearInterval(pollTimer.value)
      pollTimer.value = null
    }
    setTimeout(() => {
      router.replace('/owner/bills')
    }, 2000)
    return true
  } catch (e) {
    status.value = 'error'
    title.value = '支付宝支付确认失败'
    detail.value = e.response?.data?.detail || e.message || '请返回账单页重试'
    toast.error(detail.value)
    if (pollTimer.value) {
      clearInterval(pollTimer.value)
      pollTimer.value = null
    }
    return false
  } finally {
    loading.value = false
  }
}

function startPolling() {
  if (pollTimer.value) return
  pollCount.value = 0
  confirmPayment()
  pollTimer.value = setInterval(async () => {
    pollCount.value += 1
    const ok = await confirmPayment()
    if (ok || pollCount.value >= maxPollCount) {
      if (pollTimer.value) {
        clearInterval(pollTimer.value)
        pollTimer.value = null
      }
      if (!ok && status.value === 'pending') {
        status.value = 'error'
        title.value = '支付结果超时'
        detail.value = '系统已连续查询一段时间，仍未确认支付成功，请稍后在账单页手动刷新查看。'
        toast.warn(detail.value)
      }
    }
  }, 3000)
}

onMounted(startPolling)

onBeforeUnmount(() => {
  if (pollTimer.value) {
    clearInterval(pollTimer.value)
    pollTimer.value = null
  }
})
</script>

<template>
  <div class="rpms-panel recharge-result">
    <p class="recharge-result__eyebrow">支付宝缴费结果</p>
    <h2 class="recharge-result__title">{{ title }}</h2>
    <p class="recharge-result__desc">{{ detail }}</p>

    <div v-if="loading" class="rpms-muted">正在校验交易信息...</div>
    <div v-else-if="status === 'pending'" class="rpms-muted">支付处理中，页面将自动重复查询结果...</div>

    <div v-else class="recharge-result__card" :class="`recharge-result__card--${status}`">
      <div class="recharge-result__row">
        <span>订单号</span>
        <strong>{{ outTradeNo || '--' }}</strong>
      </div>
      <div class="recharge-result__row">
        <span>支付宝交易号</span>
        <strong>{{ tradeNo || '--' }}</strong>
      </div>
      <div class="recharge-result__row" v-if="bill">
        <span>账期</span>
        <strong>{{ bill.year_month }}</strong>
      </div>
      <div class="recharge-result__row" v-if="bill">
        <span>金额</span>
        <strong>{{ bill.amount }}</strong>
      </div>
      <div class="recharge-result__row" v-if="payment">
        <span>支付方式</span>
        <strong>{{ paymentMethodLabel(payment.payment_method) }}</strong>
      </div>
    </div>

    <div class="recharge-result__actions">
      <button type="button" class="rpms-btn rpms-btn--primary" @click="router.replace('/owner/bills')">
        返回账单页
      </button>
      <button type="button" class="rpms-btn rpms-btn--secondary" @click="confirmPayment">
        重新确认
      </button>
    </div>
  </div>
</template>

<style scoped>
.recharge-result {
  max-width: 760px;
  margin: 32px auto;
}

.recharge-result__eyebrow {
  margin: 0 0 10px;
  color: var(--rpms-primary, #2a6ebb);
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.12em;
}

.recharge-result__title {
  margin: 0 0 10px;
  font-size: 1.35rem;
  color: var(--rpms-text, #0f172a);
}

.recharge-result__desc {
  margin: 0 0 18px;
  color: var(--rpms-text-muted, #64748b);
  line-height: 1.7;
}

.recharge-result__card {
  padding: 18px 20px;
  border-radius: 16px;
  border: 1px solid var(--rpms-card-border);
  background: #fff;
  display: grid;
  gap: 12px;
}

.recharge-result__card--success {
  border-color: rgba(22, 163, 74, 0.22);
  background: rgba(236, 253, 245, 0.65);
}

.recharge-result__card--error {
  border-color: rgba(220, 38, 38, 0.22);
  background: rgba(254, 242, 242, 0.7);
}

.recharge-result__row {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  color: var(--rpms-text, #0f172a);
}

.recharge-result__row span {
  color: var(--rpms-text-muted, #64748b);
}

.recharge-result__actions {
  display: flex;
  gap: 12px;
  margin-top: 18px;
}
</style>
