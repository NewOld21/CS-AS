<script setup lang="ts">
import { computed } from 'vue'
import type { Source } from '../quiz/api'
const props = defineProps<{ content: string; sources?: Source[] }>()
const emit = defineEmits<{ evidence: [source: Source] }>()
const blocks = computed(() =>
  props.content.split(/```/).map((content, index) => ({ content, code: index % 2 === 1 })),
)
</script>
<template>
  <div class="safe-answer">
    <template v-for="(block, index) in blocks" :key="index">
      <pre v-if="block.code"><code>{{ block.content.replace(/^\w+\n/, '') }}</code></pre>
      <p v-else>
        <template v-for="(part, partIndex) in block.content.split(/(\[\d+\])/g)" :key="partIndex"
          ><button
            v-if="/^\[\d+\]$/.test(part) && sources?.[Number(part.slice(1, -1)) - 1]"
            type="button"
            :aria-label="`?? ${part} ??`"
            @click="emit('evidence', sources![Number(part.slice(1, -1)) - 1]!)"
          >
            {{ part }}</button
          ><template v-else>{{ part }}</template></template
        >
      </p>
    </template>
  </div>
</template>
