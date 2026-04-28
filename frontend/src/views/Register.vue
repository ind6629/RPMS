<script setup>
import '@/assets/auth-split.css'
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import http from '@/api/http'
import { useToast } from '@/utils/toast'

const router = useRouter()

const username = ref('')
const password = ref('')
const email = ref('')
const phone = ref('')
const captcha = ref('')
const expression = ref('')
const error = ref('')
const msg = ref('')
const loading = ref(false)
const toast = useToast()

async function loadCaptcha() {
  const { data } = await http.get('/api/users/captcha/')
  expression.value = data.expression
}

onMounted(async () => {
  await loadCaptcha()
})

async function submit() {
  error.value = ''
  msg.value = ''
  loading.value = true
  try {
    await http.post('/api/users/register/', {
      username: username.value,
      password: password.value,
      email: email.value,
      phone: phone.value,
      captcha: captcha.value,
    })
    msg.value = '注册成功，即将跳转登录'
    toast.success('注册成功，即将跳转登录')
    setTimeout(() => router.push('/login'), 900)
  } catch (e) {
    error.value =
      e.response?.data?.error ||
      (e.response?.data && JSON.stringify(e.response.data)) ||
      '注册失败'
    toast.error(error.value)
    await loadCaptcha()
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="auth-split">
    <aside class="auth-split__promo auth-split__promo--register" aria-hidden="false">
      <div class="auth-split__promo-bg" />
      <div class="auth-split__promo-inner">
        <p class="auth-split__eyebrow">业主专属入口</p>
        <h2 class="auth-split__headline">加入智慧社区</h2>
        <p class="auth-split__lead">
          注册后可查看名下房产、在线报修、缴纳费用，并随时提交投诉建议，物业将及时跟进。
        </p>
        <ul class="auth-split__bullets">
          <li>
            <span class="auth-split__dot" />
            信息加密传输，保障账号安全
          </li>
          <li>
            <span class="auth-split__dot" />
            办理进度透明可查
          </li>
          <li>
            <span class="auth-split__dot" />
            与物业后台数据实时同步
          </li>
        </ul>
      </div>
    </aside>
    <section class="auth-split__form-wrap">
      <div class="auth-split__form-card">
        <div class="auth-split__form-head">
          <h1 class="auth-split__title">业主注册</h1>
          <p class="auth-split__subtitle">填写以下信息完成开户</p>
        </div>
        <form class="auth-form" @submit.prevent="submit">
          <label class="auth-form__label" for="reg-user">用户名</label>
          <input id="reg-user" v-model="username" class="auth-form__input" placeholder="登录用户名" />
          <label class="auth-form__label" for="reg-pass">密码（至少 6 位）</label>
          <input
            id="reg-pass"
            v-model="password"
            class="auth-form__input"
            type="password"
            placeholder="设置登录密码"
          />
          <label class="auth-form__label" for="reg-email">邮箱</label>
          <input id="reg-email" v-model="email" class="auth-form__input" type="email" placeholder="常用邮箱" />
          <label class="auth-form__label" for="reg-phone">手机</label>
          <input id="reg-phone" v-model="phone" class="auth-form__input" placeholder="手机号码" />
          <label class="auth-form__label" for="reg-cap">验证码</label>
          <p class="auth-form__captcha-line" id="reg-cap-desc">{{ expression }}</p>
          <input
            id="reg-cap"
            v-model="captcha"
            class="auth-form__input"
            placeholder="填写计算结果"
            aria-describedby="reg-cap-desc"
          />
          <p v-if="error" class="auth-form__msg auth-form__msg--err" role="alert">{{ error }}</p>
          <p v-if="msg" class="auth-form__msg auth-form__msg--ok" role="status">{{ msg }}</p>
          <button type="submit" class="auth-form__submit auth-form__submit--accent" :disabled="loading">
            {{ loading ? '提交中…' : '注册' }}
          </button>
          <p class="auth-form__footer">
            已有账号？
            <RouterLink class="auth-form__link" to="/login">返回登录</RouterLink>
          </p>
        </form>
      </div>
    </section>
  </div>
</template>
