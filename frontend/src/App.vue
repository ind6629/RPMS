<script setup>
import RpmsToastHost from '@/components/RpmsToastHost.vue'
</script>

<template>
  <div>
    <RouterView />
    <RpmsToastHost />
  </div>
</template>

<style>
*,
*::before,
*::after {
  box-sizing: border-box;
}

html {
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

body {
  margin: 0;
  font-family:
    system-ui,
    -apple-system,
    'Segoe UI',
    Roboto,
    'PingFang SC',
    'Microsoft YaHei',
    'Helvetica Neue',
    Arial,
    sans-serif;
  color: #0f172a;
}
</style>
