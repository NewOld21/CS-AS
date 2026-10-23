<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from 'vue'
import { safeSourceUrl, type Source } from '../quiz/api'

defineProps<{ source: Source; sources: Source[] }>()
const emit = defineEmits<{ close: []; select: [source: Source] }>()
const dialog = ref<HTMLDialogElement>()
let previous: HTMLElement | null = null
onMounted(() => {
  previous = document.activeElement as HTMLElement | null
  dialog.value?.showModal()
})
onBeforeUnmount(() => {
  dialog.value?.close()
  previous?.focus()
})
</script>

<template>
  <dialog
    ref="dialog"
    class="evidence-panel"
    aria-labelledby="evidence-title"
    @cancel.prevent="emit('close')"
  >
    <header>
      <h2 id="evidence-title">근거 자료</h2>
      <button type="button" aria-label="근거 패널 닫기" @click="emit('close')">×</button>
    </header>
    <nav v-if="sources.length > 1" aria-label="근거 전환">
      <button
        v-for="(item, index) in sources"
        :key="item.chunk_id"
        type="button"
        :aria-pressed="item.chunk_id === source.chunk_id"
        @click="emit('select', item)"
      >
        [{{ index + 1 }}] {{ item.title }}
      </button>
    </nav>
    <h3>{{ source.title }}</h3>
    <dl>
      <dt>출처</dt>
      <dd>{{ source.source_id }}</dd>
      <dt>카테고리</dt>
      <dd>{{ source.category || '정보 없음' }}</dd>
      <dt>기술 버전</dt>
      <dd>{{ source.technology_version || '정보 없음' }}</dd>
      <dt>리비전</dt>
      <dd>{{ source.revision }}</dd>
      <dt>문서 위치</dt>
      <dd>{{ source.locator }}</dd>
    </dl>
    <h4>관련 내용</h4>
    <p v-if="source.evidence_text" class="evidence-text">{{ source.evidence_text }}</p>
    <p v-else role="status">
      이전 근거 본문을 확인할 수 없습니다. 현재 문서의 내용으로 대체하지 않습니다.
    </p>
    <a
      v-if="safeSourceUrl(source.url)"
      :href="safeSourceUrl(source.url)!"
      target="_blank"
      rel="noopener noreferrer"
      >원본 문서 열기 ↗<small>{{ source.url }}</small></a
    >
    <p v-else>안전하지 않은 원본 URL은 열 수 없습니다.</p>
  </dialog>
</template>

<style scoped>
.evidence-panel {
  width: min(640px, calc(100vw - 2rem));
  max-height: 85dvh;
  overflow: auto;
  padding: 1.5rem;
  border: 1px solid var(--line, #536074);
  border-radius: 18px;
  background: var(--surface, #151e30);
  color: inherit;
}
.evidence-panel::backdrop {
  background: #0009;
}
header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
button {
  color: inherit;
  background: transparent;
  border: 1px solid currentColor;
  border-radius: 8px;
  padding: 0.4rem 0.7rem;
  cursor: pointer;
}
nav {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}
dd,
small {
  overflow-wrap: anywhere;
}
small {
  display: block;
}
.evidence-text {
  white-space: pre-wrap;
  line-height: 1.8;
}
@media (max-width: 600px) {
  .evidence-panel {
    margin: auto 0 0;
    width: 100%;
    max-width: 100%;
    max-height: 90dvh;
    border-radius: 18px 18px 0 0;
  }
}
</style>
