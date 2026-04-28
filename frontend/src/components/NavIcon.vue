<script setup>
defineProps({
  name: {
    type: String,
    required: true,
  },
})
</script>

<template>
  <svg
    class="rpms-nav-icon"
    viewBox="0 0 24 24"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
    aria-hidden="true"
  >
    <template v-if="name === 'home'">
      <path
        d="M3 10.5L12 3l9 7.5V21a1 1 0 01-1 1h-5v-6H9v6H4a1 1 0 01-1-1v-10.5z"
        stroke="currentColor"
        stroke-width="1.75"
        stroke-linejoin="round"
      />
    </template>
    <template v-else-if="name === 'properties'">
      <path
        d="M4 21V8l8-5 8 5v13M9 21v-6h6v6"
        stroke="currentColor"
        stroke-width="1.75"
        stroke-linecap="round"
        stroke-linejoin="round"
      />
    </template>
    <template v-else-if="name === 'repairs'">
      <path
        d="M14.7 6.3a1 1 0 000 1.4l1.6 1.6a1 1 0 001.4 0l3-3-4-4-3 3zM12 3l-1.5 1.5M4 20l4.5-4.5M3 21l5-5"
        stroke="currentColor"
        stroke-width="1.75"
        stroke-linecap="round"
        stroke-linejoin="round"
      />
    </template>
    <template v-else-if="name === 'bills'">
      <path
        d="M12 2v20M17 5H9.5a3.5 3.5 0 000 7h5a3.5 3.5 0 010 7H6"
        stroke="currentColor"
        stroke-width="1.75"
        stroke-linecap="round"
        stroke-linejoin="round"
      />
    </template>
    <template v-else-if="name === 'complaints'">
      <path
        d="M4 4h16v12H9l-4 4V4z"
        stroke="currentColor"
        stroke-width="1.75"
        stroke-linejoin="round"
      />
    </template>
    <template v-else-if="name === 'news'">
      <path
        d="M4 11v9h16v-9M4 11V6a2 2 0 012-2h12a2 2 0 012 2v5M8 7h1M12 7h1M16 7h1M8 11h8"
        stroke="currentColor"
        stroke-width="1.75"
        stroke-linecap="round"
      />
    </template>
    <template v-else-if="name === 'profile'">
      <path
        d="M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2M12 11a4 4 0 100-8 4 4 0 000 8z"
        stroke="currentColor"
        stroke-width="1.75"
        stroke-linecap="round"
      />
    </template>
    <template v-else-if="name === 'users'">
      <path
        d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2M9 11a4 4 0 100-8 4 4 0 000 8zm14 2v-2a4 4 0 00-3-3.87M16 3.13a4 4 0 010 7.75"
        stroke="currentColor"
        stroke-width="1.75"
        stroke-linecap="round"
      />
    </template>
    <template v-else-if="name === 'clipboard'">
      <path
        d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9h6m-6 4h6"
        stroke="currentColor"
        stroke-width="1.75"
        stroke-linecap="round"
      />
    </template>
    <template v-else-if="name === 'star'">
      <path
        d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"
        stroke="currentColor"
        stroke-width="1.75"
        stroke-linejoin="round"
      />
    </template>
    <template v-else-if="name === 'logs'">
      <path
        d="M8 6h13M8 12h13M8 18h13M3 6h.01M3 12h.01M3 18h.01"
        stroke="currentColor"
        stroke-width="1.75"
        stroke-linecap="round"
      />
    </template>
    <template v-else>
      <circle cx="12" cy="12" r="9" stroke="currentColor" stroke-width="1.75" />
    </template>
  </svg>
</template>

<style scoped>
.rpms-nav-icon {
  width: 22px;
  height: 22px;
  flex-shrink: 0;
}
</style>
