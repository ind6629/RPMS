const ROLE_LABELS = {
  owner: '业主',
  employee: '员工',
  admin: '管理员',
}

const STATUS_LABELS = {
  pending: '待处理',
  processing: '处理中',
  completed: '已完成',
  cancelled: '已取消',
  paid: '已缴费',
  unpaid: '未缴费',
  overdue: '已逾期',
  draft: '草稿',
  published: '已发布',
}

const PAYMENT_METHOD_LABELS = {
  alipay: '支付宝',
  wechat: '微信支付',
  cash: '现金',
  bank_transfer: '银行转账',
}

const CN_DATE_FORMATTER = new Intl.DateTimeFormat('zh-CN', {
  timeZone: 'Asia/Shanghai',
  year: 'numeric',
  month: '2-digit',
  day: '2-digit',
})

const CN_DATETIME_FORMATTER = new Intl.DateTimeFormat('zh-CN', {
  timeZone: 'Asia/Shanghai',
  year: 'numeric',
  month: '2-digit',
  day: '2-digit',
  hour: '2-digit',
  minute: '2-digit',
  hour12: false,
})

function isDateOnly(value) {
  return /^\d{4}-\d{2}-\d{2}$/.test(String(value || ''))
}

function normalizeDateText(value, formatter) {
  if (!value) return '--'
  if (isDateOnly(value)) return String(value)
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return String(value)
  return formatter.format(date).replace(/\//g, '-')
}

export function roleLabel(value) {
  return ROLE_LABELS[value] || value || '--'
}

export function statusLabel(value) {
  return STATUS_LABELS[value] || value || '--'
}

export function paymentMethodLabel(value) {
  return PAYMENT_METHOD_LABELS[value] || value || '--'
}

export function formatDateCN(value) {
  return normalizeDateText(value, CN_DATE_FORMATTER)
}

export function formatDateTimeCN(value) {
  return normalizeDateText(value, CN_DATETIME_FORMATTER)
}

export function toLocalDateInput(value = new Date()) {
  const date = value instanceof Date ? new Date(value) : new Date(value)
  if (Number.isNaN(date.getTime())) return ''
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}
