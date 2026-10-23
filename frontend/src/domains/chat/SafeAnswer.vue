<script setup lang="ts">
import { computed, ref } from 'vue'
import type { Source } from '../quiz/api'
const props = defineProps<{ content: string; sources?: Source[] }>()
const emit = defineEmits<{ evidence: [source: Source] }>()
const copied = ref(-1)
async function copy(content: string, index: number) {
  try {
    await navigator.clipboard.writeText(content.replace(/^\w+\n/, ''))
    copied.value = index
  } catch {
    copied.value = -1
  }
}
const blocks = computed(() =>
  props.content.split(/```/).map((content, index) => ({ content, code: index % 2 === 1 })),
)
</script>
<template>
  <div class="safe-answer">
    <template v-for="(block, index) in blocks" :key="index">
      <div v-if="block.code" class="code-block">
        <button type="button" @click="copy(block.content, index)">
          {{ copied === index ? '복사됨' : '코드 복사' }}
        </button>
        <pre><code>{{ block.content.replace(/^\w+\n/, '') }}</code></pre>
      </div>
      <component
        :is="/^#{1,3} /.test(line) ? 'h4' : 'p'"
        v-for="(line, lineIndex) in block.code ? [] : block.content.split('\n')"
        :key="`${index}-${lineIndex}`"
      >
        <template
          v-for="(part, partIndex) in line
            .replace(/^#{1,3} /, '')
            .split(/(\[\d+\]|\*\*[^*]+\*\*|`[^`]+`)/g)"
          :key="partIndex"
          ><button
            v-if="/^\[\d+\]$/.test(part) && sources?.[Number(part.slice(1, -1)) - 1]"
            type="button"
            :aria-label="`근거 ${part} 보기`"
            @click="emit('evidence', sources![Number(part.slice(1, -1)) - 1]!)"
          >
            {{ part }}</button
          ><strong v-else-if="part.startsWith('**')">{{ part.slice(2, -2) }}</strong
          ><code v-else-if="part.startsWith('`')">{{ part.slice(1, -1) }}</code
          ><template v-else>{{ part }}</template></template
        >
      </component>
    </template>
  </div>
</template>
<style scoped>
.code-block {
  min-width: 0;
}
.code-block pre {
  overflow-x: auto;
  max-width: 100%;
}
.code-block > button {
  color: var(--color-accent);
  background: transparent;
  border: 1px solid var(--color-line);
  padding: var(--space-2) var(--space-3);
  border-radius: var(--radius-sm);
}
.safe-answer p {
  white-space: pre-wrap;
}
</style>
