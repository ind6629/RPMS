<script setup>
import '@/assets/auth-split.css'
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import http from '@/api/http'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const auth = useAuthStore()

const username = ref('')
const password = ref('')
const role = ref('owner')
const captcha = ref('')
const expression = ref('')
const captchaArt = ref({ chars: [], lines: [], dots: [], seed: 0 })
const error = ref('')
const loading = ref(false)

function rand(min, max) {
  return min + Math.random() * (max - min)
}

function buildCaptchaArt(text) {
  const base = String(text || '')
  const palette = ['#1d4ed8', '#0f766e', '#b45309', '#7c3aed', '#c2410c', '#ef4444']
  let cursor = 20
  const chars = [...base].map((ch, idx) => {
    const isSpace = ch === ' '
    const advance = isSpace ? 8 : rand(14, 20)
    const item = {
      ch,
      x: cursor + rand(-2, 2),
      y: rand(34, 42),
      rotate: isSpace ? rand(-8, 8) : rand(-28, 28),
      size: isSpace ? 18 : rand(22, 30),
      color: palette[idx % palette.length],
      blur: isSpace ? 0 : rand(0, 0.8),
    }
    cursor += advance
    return item
  })

  captchaArt.value = {
    seed: Math.random(),
    chars,
    lines: Array.from({ length: 6 }, () => ({
      x1: rand(0, 180),
      y1: rand(0, 60),
      x2: rand(0, 180),
      y2: rand(0, 60),
      color: `rgba(${Math.floor(rand(70, 180))}, ${Math.floor(rand(90, 190))}, ${Math.floor(rand(110, 220))}, ${rand(0.35, 0.65).toFixed(2)})`,
      width: rand(1.2, 2.2),
    })),
    dots: Array.from({ length: 26 }, () => ({
      cx: rand(0, 180),
      cy: rand(0, 60),
      r: rand(0.6, 1.5),
      color: `rgba(${Math.floor(rand(80, 170))}, ${Math.floor(rand(80, 170))}, ${Math.floor(rand(80, 170))}, ${rand(0.22, 0.5).toFixed(2)})`,
    })),
  }
}

async function loadCaptcha() {
  const { data } = await http.get('/api/users/captcha/')
  expression.value = data.expression
  buildCaptchaArt(data.expression)
}

onMounted(async () => {
  try {
    await loadCaptcha()
  } catch {
    expression.value = '（验证码加载失败，请刷新）'
  }
})

async function submit() {
  error.value = ''
  loading.value = true
  try {
    await auth.login({
      username: username.value,
      password: password.value,
      role: role.value,
      captcha: captcha.value,
    })
    router.replace(auth.redirectPathByRole())
  } catch (e) {
    error.value = e.response?.data?.error || e.response?.data?.detail || '登录失败'
    await loadCaptcha()
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="auth-split">
    <aside class="auth-split__promo" aria-hidden="false">
      <div class="auth-split__promo-bg" />
      <div class="auth-split__promo-inner">
        <p class="auth-split__eyebrow">RPMS · 住宅物业管理系统</p>
        <h2 class="auth-split__headline">统一平台，服务每一户</h2>
        <p class="auth-split__lead">
          报修、缴费、公告与投诉建议集中办理，降低沟通成本，提升响应效率。
        </p>
        <ul class="auth-split__bullets">
          <li>
            <span class="auth-split__dot" />
            多角色权限，数据隔离更安全
          </li>
          <li>
            <span class="auth-split__dot" />
            工单与账单可追溯，管理更省心
          </li>
          <li>
            <span class="auth-split__dot" />
            界面简洁清晰，上手即用
          </li>
        </ul>
      </div>
    </aside>
    <section class="auth-split__form-wrap">
      <div class="auth-split__form-card">
        <div class="auth-split__form-head">
          <h1 class="auth-split__title">欢迎回来</h1>
          <p class="auth-split__subtitle">请使用账号登录系统</p>
        </div>
        <form class="auth-form" @submit.prevent="submit">
          <label class="auth-form__label" for="login-user">用户名</label>
          <input
            id="login-user"
            v-model="username"
            class="auth-form__input"
            name="username"
            autocomplete="username"
            placeholder="请输入用户名"
          />
          <label class="auth-form__label" for="login-pass">密码</label>
          <input
            id="login-pass"
            v-model="password"
            class="auth-form__input"
            name="password"
            type="password"
            autocomplete="current-password"
            placeholder="请输入密码"
          />
          <label class="auth-form__label">角色</label>
          <div class="rpms-form-row" style="margin: 0 0 2px">
            <label class="rpms-muted" style="display: inline-flex; align-items: center; gap: 6px">
              <input v-model="role" type="radio" value="owner" />
              业主
            </label>
            <label class="rpms-muted" style="display: inline-flex; align-items: center; gap: 6px">
              <input v-model="role" type="radio" value="employee" />
              员工
            </label>
            <label class="rpms-muted" style="display: inline-flex; align-items: center; gap: 6px">
              <input v-model="role" type="radio" value="admin" />
              管理员
            </label>
          </div>
          <label class="auth-form__label" for="login-cap">验证码</label>
          <div id="login-cap-desc" class="auth-form__captcha-wrap">
            <button
              type="button"
              class="auth-form__captcha-button"
              :aria-label="`验证码：${expression}，点击刷新`"
              title="点击刷新验证码"
              @click="loadCaptcha"
            >
              <svg class="auth-form__captcha-svg" viewBox="0 0 180 60" role="img" aria-label="验证码图片">
                <defs>
                  <linearGradient id="captchaBg" x1="0" x2="1" y1="0" y2="1">
                    <stop offset="0%" stop-color="#eef4ff" />
                    <stop offset="100%" stop-color="#ffffff" />
                  </linearGradient>
                  <filter id="captchaBlur" x="-20%" y="-20%" width="140%" height="140%">
                    <feGaussianBlur stdDeviation="0.45" />
                  </filter>
                </defs>
                <rect x="0" y="0" width="180" height="60" rx="12" fill="url(#captchaBg)" />
                <path
                  v-for="(line, idx) in captchaArt.lines"
                  :key="`line-${idx}-${captchaArt.seed}`"
                  :d="`M ${line.x1} ${line.y1} L ${line.x2} ${line.y2}`"
                  :stroke="line.color"
                  :stroke-width="line.width"
                  stroke-linecap="round"
                  fill="none"
                />
                <circle
                  v-for="(dot, idx) in captchaArt.dots"
                  :key="`dot-${idx}-${captchaArt.seed}`"
                  :cx="dot.cx"
                  :cy="dot.cy"
                  :r="dot.r"
                  :fill="dot.color"
                />
                <g filter="url(#captchaBlur)">
                  <text
                    v-for="(item, idx) in captchaArt.chars"
                    :key="`char-${idx}-${captchaArt.seed}`"
                    :x="item.x"
                    :y="item.y"
                    :fill="item.color"
                    :font-size="item.size"
                    font-weight="800"
                    text-anchor="middle"
                    dominant-baseline="middle"
                    :transform="`rotate(${item.rotate} ${item.x} ${item.y}) skewX(${rand(-10, 10)})`"
                    style="font-family: Arial, 'Microsoft YaHei', sans-serif; letter-spacing: 0.02em"
                  >
                    {{ item.ch }}
                  </text>
                </g>
                <rect x="0" y="0" width="180" height="60" rx="12" fill="transparent" stroke="rgba(148, 163, 184, 0.5)" />
              </svg>
            </button>
            <p class="auth-form__captcha-tip">点击图片可刷新验证码</p>
          </div>
          <input
            id="login-cap"
            v-model="captcha"
            class="auth-form__input"
            name="captcha"
            placeholder="请输入图中结果"
            autocomplete="off"
            aria-describedby="login-cap-desc"
          />
          <p v-if="error" class="auth-form__msg auth-form__msg--err" role="alert">{{ error }}</p>
          <button type="submit" class="auth-form__submit" :disabled="loading">
            {{ loading ? '登录中…' : '登录' }}
          </button>
          <p class="auth-form__footer">
            没有账号？
            <RouterLink class="auth-form__link" to="/register">注册业主账号</RouterLink>
          </p>
        </form>
      </div>
    </section>
  </div>
</template>

<style scoped>
.auth-form__captcha-wrap {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin: 4px 0 10px;
}

.auth-form__captcha-button {
  appearance: none;
  border: 0;
  padding: 0;
  background: transparent;
  cursor: pointer;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 8px 22px rgba(15, 23, 42, 0.08);
}

.auth-form__captcha-button:focus-visible {
  outline: 2px solid rgba(42, 110, 187, 0.55);
  outline-offset: 2px;
}

.auth-form__captcha-svg {
  display: block;
  width: 100%;
  max-width: 260px;
  height: 60px;
}

.auth-form__captcha-tip {
  margin: 0;
  font-size: 12px;
  color: var(--rpms-text-muted, #64748b);
}

.auth-form__captcha-box {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 2px;
  min-height: 46px;
  margin: 4px 0 10px;
  padding: 8px 12px;
  border-radius: 12px;
  border: 1px solid rgba(148, 163, 184, 0.45);
  background:
    linear-gradient(135deg, rgba(42, 110, 187, 0.08), rgba(255, 255, 255, 0.94)),
    repeating-linear-gradient(
      135deg,
      rgba(148, 163, 184, 0.08) 0,
      rgba(148, 163, 184, 0.08) 6px,
      transparent 6px,
      transparent 12px
    );
  overflow: hidden;
  user-select: none;
}

.auth-form__captcha-char {
  position: relative;
  display: inline-block;
  font-size: 22px;
  font-weight: 800;
  letter-spacing: 0.08em;
  line-height: 1;
  text-shadow: 0 1px 0 rgba(255, 255, 255, 0.55);
  animation: captchaFloat 2.8s ease-in-out infinite;
}

.auth-form__captcha-noise {
  position: absolute;
  inset: 0;
  pointer-events: none;
}

.auth-form__captcha-noise--1 {
  background:
    radial-gradient(circle at 18% 25%, rgba(42, 110, 187, 0.22) 0 1px, transparent 1.5px),
    radial-gradient(circle at 72% 35%, rgba(124, 58, 237, 0.2) 0 1px, transparent 1.5px),
    radial-gradient(circle at 56% 72%, rgba(22, 163, 74, 0.16) 0 1px, transparent 1.5px);
  opacity: 0.7;
}

.auth-form__captcha-noise--2 {
  background: linear-gradient(115deg, transparent 46%, rgba(15, 23, 42, 0.12) 47%, transparent 48%);
  opacity: 0.55;
}

.auth-form__captcha-noise--3 {
  background: linear-gradient(25deg, transparent 22%, rgba(255, 255, 255, 0.55) 23%, transparent 24%);
  opacity: 0.45;
}

@keyframes captchaFloat {
  0%,
  100% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(-1px);
  }
}
</style>
