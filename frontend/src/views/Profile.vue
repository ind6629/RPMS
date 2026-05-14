<script setup>
import { computed, onMounted, ref } from 'vue'
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
const avatarPreview = ref('')
const avatarViewerOpen = ref(false)

const currentAvatarUrl = computed(() => avatarPreview.value || auth.user?.avatar || '')

onMounted(async () => {
  await auth.bootstrap()
  phone.value = auth.user?.phone || ''
  email.value = auth.user?.email || ''
})

function onAvatarChange(event) {
  const file = event.target?.files?.[0]
  if (avatarPreview.value) {
    URL.revokeObjectURL(avatarPreview.value)
    avatarPreview.value = ''
  }
  if (file) {
    avatarPreview.value = URL.createObjectURL(file)
  }
}

function openAvatarViewer() {
  if (!currentAvatarUrl.value) return
  avatarViewerOpen.value = true
}

function closeAvatarViewer() {
  avatarViewerOpen.value = false
}

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
    if (avatarPreview.value) {
      URL.revokeObjectURL(avatarPreview.value)
      avatarPreview.value = ''
    }
    if (el) el.value = ''
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

        <div class="profile-avatar">
          <button
            type="button"
            class="profile-avatar__frame profile-avatar__trigger"
            :disabled="!currentAvatarUrl"
            @click="openAvatarViewer"
          >
            <img v-if="currentAvatarUrl" :src="currentAvatarUrl" alt="当前头像" class="profile-avatar__image" />
            <div v-else class="profile-avatar__placeholder" aria-hidden="true">
              {{ auth.user?.username?.slice(0, 1)?.toUpperCase() || '?' }}
            </div>
          </button>
          <p class="rpms-muted profile-avatar__caption">
            {{ avatarPreview ? '预览中的新头像' : '当前头像，点击可放大' }}
          </p>
        </div>

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
          <input id="avatar" type="file" accept="image/*" class="rpms-input" @change="onAvatarChange" />
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

    <div v-if="avatarViewerOpen && currentAvatarUrl" class="profile-avatar-viewer" @click.self="closeAvatarViewer">
      <button type="button" class="profile-avatar-viewer__close" aria-label="关闭头像预览" @click="closeAvatarViewer">
        ×
      </button>
      <img :src="currentAvatarUrl" alt="头像大图预览" class="profile-avatar-viewer__image" />
    </div>
  </div>
</template>

<style scoped>
.profile-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(280px, 1fr));
  gap: 18px;
}

.profile-avatar {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 10px;
  margin-bottom: 18px;
}

.profile-avatar__frame {
  width: 96px;
  height: 96px;
  overflow: hidden;
  border-radius: 20px;
  border: 1px solid rgba(15, 23, 42, 0.08);
  box-shadow: 0 12px 28px rgba(15, 23, 42, 0.12);
  flex: 0 0 96px;
  background: #fff;
}

.profile-avatar__trigger {
  padding: 0;
  cursor: pointer;
}

.profile-avatar__trigger:disabled {
  cursor: default;
}

.profile-avatar__image,
.profile-avatar__placeholder {
  width: 100%;
  height: 100%;
  max-width: 96px;
  max-height: 96px;
}

.profile-avatar__image {
  display: block;
  object-fit: cover;
}

.profile-avatar__placeholder {
  display: grid;
  place-items: center;
  background: linear-gradient(135deg, #dbeafe, #fef3c7);
  color: #1e293b;
  font-size: 32px;
  font-weight: 700;
}

.profile-avatar__caption {
  margin: 0;
}

.profile-avatar-viewer {
  position: fixed;
  inset: 0;
  z-index: 1000;
  display: grid;
  place-items: center;
  padding: 24px;
  background: rgba(15, 23, 42, 0.72);
}

.profile-avatar-viewer__image {
  max-width: min(88vw, 720px);
  max-height: 88vh;
  border-radius: 24px;
  background: #fff;
  box-shadow: 0 24px 80px rgba(15, 23, 42, 0.35);
}

.profile-avatar-viewer__close {
  position: absolute;
  top: 20px;
  right: 20px;
  width: 44px;
  height: 44px;
  border: none;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.92);
  color: #0f172a;
  font-size: 30px;
  line-height: 1;
  cursor: pointer;
}

@media (max-width: 900px) {
  .profile-grid {
    grid-template-columns: 1fr;
  }
}
</style>
