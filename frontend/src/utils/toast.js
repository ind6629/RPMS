import { readonly, reactive } from 'vue'

const state = reactive({
  items: [],
})

let nextId = 1

function formatErrorDetail(detail) {
  if (detail == null || detail === '') return ''
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail)) {
    return detail.map((item) => formatErrorDetail(item)).filter(Boolean).join('；')
  }
  if (typeof detail === 'object') {
    return Object.entries(detail)
      .map(([key, value]) => {
        const text = formatErrorDetail(value)
        return text ? `${key}: ${text}` : key
      })
      .filter(Boolean)
      .join('；')
  }
  return String(detail)
}

function removeToast(id) {
  const idx = state.items.findIndex((item) => item.id === id)
  if (idx >= 0) {
    state.items.splice(idx, 1)
  }
}

function pushToast(type, message, options = {}) {
  const id = nextId++
  const toast = {
    id,
    type,
    title: options.title || '',
    message: String(message || ''),
  }
  state.items.push(toast)

  const timeout = Number.isFinite(options.timeout) ? options.timeout : 3200
  if (timeout > 0) {
    window.setTimeout(() => {
      removeToast(id)
    }, timeout)
  }

  return id
}

export function useToast() {
  return {
    toasts: readonly(state.items),
    success(message, options = {}) {
      return pushToast('success', message, options)
    },
    error(message, options = {}) {
      return pushToast('error', message, options)
    },
    warn(message, options = {}) {
      return pushToast('warn', message, options)
    },
    info(message, options = {}) {
      return pushToast('info', message, options)
    },
    dismiss(id) {
      removeToast(id)
    },
    clear() {
      state.items.splice(0, state.items.length)
    },
    errorMessage(error, fallback = '操作失败') {
      const detail = error?.response?.data
      if (!detail) return error?.message || fallback
      if (typeof detail === 'string') return detail
      if (detail.detail) return detail.detail
      if (detail.error) return detail.error
      const formatted = formatErrorDetail(detail)
      return formatted || error?.message || fallback
    },
  }
}
