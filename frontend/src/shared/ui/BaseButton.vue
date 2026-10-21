<script setup lang="ts">
withDefaults(
  defineProps<{
    variant?: 'primary' | 'secondary' | 'quiet'
    loading?: boolean
    type?: 'button' | 'submit'
    disabled?: boolean
  }>(),
  { variant: 'primary', type: 'button' },
)
</script>
<template>
  <button
    :type="type"
    class="button"
    :class="`button--${variant}`"
    :disabled="disabled || loading"
    :aria-busy="loading || undefined"
  >
    <span v-if="loading" class="spinner" aria-hidden="true"></span><slot />
  </button>
</template>
