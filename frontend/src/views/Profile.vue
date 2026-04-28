<script setup>
import { onMounted, ref } from 'vue'
import http from '@/api/http'
import { useAuthStore } from '@/stores/auth'
import { useToast } from '@/utils/toast'

const auth = useAuthStore()
const phone = ref('')
const email = ref('')
const oldPassword = ref('')
const newPassword = ref('')
const msg = ref('')
const err = ref('')
const toast = useToast()

onMounted(async () => {
  await auth.bootstrap()
  phone.value = auth.user?.phone || ''
  email.value = auth.user?.email || ''
})

async function saveProfile() {
  msg.value = ''
  err.value = ''
  try {
    const fd = new FormData()
    fd.append('phone', phone.value)
    fd.append('email', email.value)
    const el = document.getElementById('avatar')
    if (el?.files?.[0]) fd.append('avatar', el.files[0])
    await http.patch('/api/users/accounts/update_profile/', fd)
    await auth.bootstrap()
    msg.value = '已保存'
    toast.success('资料已保存')
  } catch (e) {
    err.value = JSON.stringify(e.response?.data || e.message)
    toast.error(toast.errorMessage(e, '保存资料失败'))
  }
}

async function savePassword() {
  msg.value = ''
  err.value = ''
  try {
    await http.post('/api/users/accounts/change_password/', {
      old_password: oldPassword.value,
      new_password: newPassword.value,
    })
    msg.value = '密码已修改'
    toast.success('密码已修改')
    oldPassword.value = ''
    newPassword.value = ''
  } catch (e) {
    err.value = JSON.stringify(e.response?.data || e.message)
    toast.error(toast.errorMessage(e, '修改密码失败'))
  }
}
</script>

<template>
  <div>
    <div class="profile-grid">
      <div class="rpms-panel">
      <h2 class="rpms-panel-title">基本资料</h2>
      <p class="rpms-muted">用户名：<strong>{{ auth.user?.username }}</strong></p>
      <div class="rpms-field">
        <label>手机</label>
        <input v-model="phone" class="rpms-input" />
      </div>
      <div class="rpms-field">
        <label>邮箱</label>
        <input v-model="email" class="rpms-input" type="email" />
      </div>
      <div class="rpms-field">
        <label>头像</label>
        <input id="avatar" type="file" accept="image/*" class="rpms-input" />
      </div>
      <button type="button" class="rpms-btn rpms-btn--primary" @click="saveProfile">保存资料</button>
      </div>
      <div class="rpms-panel">
      <h2 class="rpms-panel-title">修改密码</h2>
      <div class="rpms-field">
        <label>原密码</label>
        <input v-model="oldPassword" class="rpms-input" type="password" autocomplete="current-password" />
      </div>
      <div class="rpms-field">
        <label>新密码</label>
        <input v-model="newPassword" class="rpms-input" type="password" autocomplete="new-password" />
      </div>
      <button type="button" class="rpms-btn rpms-btn--secondary" @click="savePassword">修改密码</button>
      </div>
    </div>
    <p v-if="msg" class="rpms-msg--ok">{{ msg }}</p>
    <p v-if="err" class="rpms-msg--err">{{ err }}</p>
  </div>
</template>

<style scoped>
.profile-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(280px, 1fr));
  gap: 18px;
}

@media (max-width: 900px) {
  .profile-grid {
    grid-template-columns: 1fr;
  }
}
</style>
