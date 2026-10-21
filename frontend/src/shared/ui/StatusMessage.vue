<script setup lang="ts">
defineProps<{ kind?: 'error' | 'success' | 'info' }>()
</script>
<template>
  <div
    class="status-message"
    :class="`status-message--${kind ?? 'info'}`"
    :role="kind === 'error' ? 'alert' : 'status'"
  >
    <span aria-hidden="true">{{ kind === 'error' ? '!' : kind === 'success' ? '✓' : '↗' }}</span>
    <div><slot /></div>
  </div>
</template>
