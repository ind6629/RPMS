<script setup>
import { useToast } from '@/utils/toast'

const { toasts, dismiss } = useToast()

const typeLabel = {
  success: '成功',
  error: '失败',
  warn: '提示',
  info: '信息',
}
</script>

<template>
  <Teleport to="body">
    <div class="rpms-toast-host" aria-live="polite" aria-atomic="true">
      <TransitionGroup name="rpms-toast" tag="div" class="rpms-toast-stack">
        <article v-for="toast in toasts" :key="toast.id" class="rpms-toast" :class="`rpms-toast--${toast.type}`">
          <div class="rpms-toast__bar" />
          <div class="rpms-toast__body">
            <div class="rpms-toast__head">
              <strong class="rpms-toast__title">{{ toast.title || typeLabel[toast.type] || '提示' }}</strong>
              <button type="button" class="rpms-toast__close" aria-label="关闭提示" @click="dismiss(toast.id)">
                ×
              </button>
            </div>
            <p class="rpms-toast__message">{{ toast.message }}</p>
          </div>
        </article>
      </TransitionGroup>
    </div>
  </Teleport>
</template>

<style scoped>
.rpms-toast-host {
  position: fixed;
  top: 20px;
  right: 20px;
  z-index: 9999;
  pointer-events: none;
}

.rpms-toast-stack {
  display: flex;
  flex-direction: column;
  gap: 12px;
  width: min(360px, calc(100vw - 32px));
}

.rpms-toast {
  pointer-events: auto;
  display: flex;
  align-items: stretch;
  overflow: hidden;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.96);
  border: 1px solid rgba(226, 232, 240, 0.95);
  box-shadow: 0 12px 36px rgba(15, 23, 42, 0.16);
  backdrop-filter: blur(12px);
}

.rpms-toast__bar {
  width: 5px;
  flex-shrink: 0;
}

.rpms-toast--success .rpms-toast__bar {
  background: var(--rpms-success, #16a34a);
}

.rpms-toast--error .rpms-toast__bar {
  background: var(--rpms-danger, #dc2626);
}

.rpms-toast--warn .rpms-toast__bar {
  background: var(--rpms-warning, #ea580c);
}

.rpms-toast--info .rpms-toast__bar {
  background: var(--rpms-primary, #2a6ebb);
}

.rpms-toast__body {
  flex: 1;
  padding: 12px 14px 12px 16px;
}

.rpms-toast__head {
  display: flex;
  align-items: center;
  gap: 12px;
  justify-content: space-between;
}

.rpms-toast__title {
  color: var(--rpms-text, #0f172a);
  font-size: 14px;
  font-weight: 700;
}

.rpms-toast__message {
  margin: 6px 0 0;
  color: var(--rpms-text-muted, #64748b);
  font-size: 13px;
  line-height: 1.55;
  white-space: pre-wrap;
  word-break: break-word;
}

.rpms-toast__close {
  appearance: none;
  border: 0;
  background: transparent;
  color: var(--rpms-text-muted, #64748b);
  font-size: 18px;
  line-height: 1;
  cursor: pointer;
  padding: 0 2px;
}

.rpms-toast__close:hover {
  color: var(--rpms-text, #0f172a);
}

.rpms-toast-enter-active,
.rpms-toast-leave-active {
  transition:
    transform 0.18s ease,
    opacity 0.18s ease;
}

.rpms-toast-enter-from,
.rpms-toast-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}
</style>
