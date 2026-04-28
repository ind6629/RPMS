<script setup>
import { computed } from 'vue'

const props = defineProps({
  page: { type: Number, default: 1 },
  pageSize: { type: Number, default: 10 },
  total: { type: Number, default: 0 },
})

const emit = defineEmits(['update:page', 'update:pageSize'])

const totalPages = computed(() => {
  if (props.total <= 0) return 1
  return Math.max(1, Math.ceil(props.total / props.pageSize))
})

const pageSizeOptions = [10, 20, 50, 100]

function go(p) {
  const next = Math.min(Math.max(1, p), totalPages.value)
  emit('update:page', next)
}

function onPageSizeChange(e) {
  const n = Number(e.target.value)
  emit('update:pageSize', n)
  emit('update:page', 1)
}
</script>

<template>
  <div v-if="total > 0 || page > 1" class="rpms-pagination">
    <span class="rpms-pagination__info">共 {{ total }} 条</span>
    <select :value="pageSize" aria-label="每页条数" @change="onPageSizeChange">
      <option v-for="n in pageSizeOptions" :key="n" :value="n">{{ n }} 条/页</option>
    </select>
    <button
      type="button"
      class="rpms-pagination__btn"
      :disabled="page <= 1"
      @click="go(page - 1)"
    >
      上一页
    </button>
    <span class="rpms-pagination__page">第 {{ page }} / {{ totalPages }} 页</span>
    <button
      type="button"
      class="rpms-pagination__btn"
      :disabled="page >= totalPages"
      @click="go(page + 1)"
    >
      下一页
    </button>
  </div>
</template>
