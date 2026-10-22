<script setup lang="ts">
import { computed } from 'vue'
const props = defineProps<{ content: string }>()
const blocks = computed(() =>
  props.content.split(/```/).map((content, index) => ({ content, code: index % 2 === 1 })),
)
</script>
<template>
  <div class="safe-answer">
    <template v-for="(block, index) in blocks" :key="index">
      <pre v-if="block.code"><code>{{ block.content.replace(/^\w+\n/, '') }}</code></pre>
      <p v-else>{{ block.content }}</p>
    </template>
  </div>
</template>
