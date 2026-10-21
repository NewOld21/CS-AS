<script setup lang="ts">
import { ref, watch, nextTick } from 'vue'
import BaseButton from './BaseButton.vue'
const props = defineProps<{ feature: 'quiz' | 'chat' | null }>()
const emit = defineEmits<{ close: [] }>()
const dialog = ref<HTMLDialogElement>()
let trigger: HTMLElement | null = null
watch(
  () => props.feature,
  async (feature) => {
    await nextTick()
    if (feature) {
      trigger = document.activeElement as HTMLElement
      dialog.value?.showModal()
    } else {
      dialog.value?.close()
      trigger?.focus()
    }
  },
)
</script>
<template>
  <dialog
    ref="dialog"
    class="feature-dialog"
    aria-labelledby="feature-title"
    @cancel.prevent="emit('close')"
    @click="$event.target === dialog && emit('close')"
  >
    <span class="eyebrow">NEXT DESTINATION</span>
    <h2 id="feature-title">
      {{
        feature === 'quiz' ? '퀴즈 탐험을 준비하고 있어요.' : 'AI와 만나는 공간을 준비하고 있어요.'
      }}
    </h2>
    <p>
      지금은 가입과 로그인을 이용할 수 있어요.
      {{ feature === 'quiz' ? '분야별 문제와 해설' : '근거가 있는 CS 답변' }}은 준비가 끝나면 만날
      수 있습니다.
    </p>
    <BaseButton @click="emit('close')">알겠어요 <span aria-hidden="true">↗</span></BaseButton>
  </dialog>
</template>
