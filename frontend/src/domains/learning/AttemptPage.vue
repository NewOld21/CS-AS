<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuth } from '../auth/store'
import { errorMessage } from '../auth/validation'
import { ApiError } from '../../shared/api/client'
import StatusMessage from '../../shared/ui/StatusMessage.vue'
import BaseButton from '../../shared/ui/BaseButton.vue'
import EvidencePanel from '../chat/EvidencePanel.vue'
import SafeAnswer from '../chat/SafeAnswer.vue'
import { getQuiz, createContextChat, type Attempt, type Source } from '../quiz/api'
import { getAttempt, timestamp } from './api'

const route = useRoute()
const router = useRouter()
const auth = useAuth()
const attempt = ref<Attempt | null>(null)
const loading = ref(true)
const failure = ref('')
const retryable = ref(false)
const evidence = ref<Source | null>(null)
const contextBusy = ref(false)
async function load() {
  loading.value = true
  failure.value = ''
  retryable.value = false
  try {
    await auth.restore()
    if (!auth.user) {
      await router.replace('/login')
      return
    }
    attempt.value = await getAttempt(String(route.params.attemptId))
    try {
      await getQuiz(attempt.value.quiz.id)
      retryable.value = true
    } catch (error) {
      if (!(error instanceof ApiError && error.status === 404)) throw error
    }
  } catch (error) {
    if (error instanceof ApiError && error.status === 401) await router.replace('/login')
    failure.value = errorMessage(error)
  } finally {
    loading.value = false
  }
}
async function ask() {
  if (!attempt.value || contextBusy.value) return
  contextBusy.value = true
  try {
    const session = await createContextChat(attempt.value.quiz.id, attempt.value.id)
    await router.push({ path: '/learn', query: { chat_session_id: session.id } })
  } catch (error) {
    failure.value = errorMessage(error)
  } finally {
    contextBusy.value = false
  }
}
onMounted(load)
</script>
<template>
  <main id="main" class="account-page attempt-history" tabindex="-1">
    <p class="eyebrow">A SAVED LEARNING MOMENT</p>
    <h1>그때의 풀이, 그대로.</h1>
    <RouterLink to="/me">← 풀이 이력</RouterLink>
    <p v-if="loading" role="status">풀이 결과를 복원하고 있어요.</p>
    <div v-else-if="failure && !attempt">
      <StatusMessage kind="error">{{ failure }}</StatusMessage
      ><BaseButton variant="secondary" @click="load">다시 불러오기</BaseButton>
    </div>
    <article v-else-if="attempt" class="quiz-card">
      <p>
        {{ attempt.quiz.origin === 'AI_GENERATED' ? 'AI 생성 문제' : '일반 문제' }} · v{{
          attempt.quiz.version
        }}
        · <time :datetime="attempt.submitted_at">{{ timestamp(attempt.submitted_at) }}</time>
      </p>
      <h2>{{ attempt.quiz.stem }}</h2>
      <strong>{{ attempt.is_correct ? '당시 정답' : '당시 오답' }}</strong>
      <ol class="saved-options">
        <li v-for="option in attempt.quiz.options" :key="option.id">
          <span>{{ option.text }}</span
          ><strong v-if="option.id === attempt.selected_option_id">선택한 답</strong
          ><strong v-if="option.id === attempt.correct_option_id">당시 정답</strong>
        </li>
      </ol>
      <h3>당시 해설</h3>
      <SafeAnswer
        :content="attempt.explanation"
        :sources="attempt.sources"
        @evidence="evidence = $event"
      />
      <button
        v-for="source in attempt.sources"
        :key="source.chunk_id"
        type="button"
        @click="evidence = source"
      >
        {{ source.title }} · 근거 보기
      </button>
      <StatusMessage v-if="failure" kind="error">{{ failure }}</StatusMessage>
      <p v-if="!retryable">
        이 문제 버전은 현재 다시 풀 수 없습니다. 저장된 결과는 계속 확인할 수 있습니다.
      </p>
      <div class="quiz-actions">
        <RouterLink
          v-if="retryable"
          class="button button--primary"
          :to="{
            path: '/learn',
            query: { quiz_id: attempt.quiz.id, retry_of_attempt_id: attempt.id },
          }"
          >다시 풀기</RouterLink
        ><BaseButton variant="secondary" :loading="contextBusy" @click="ask"
          >이 풀이로 AS 질문</BaseButton
        >
      </div>
    </article>
    <EvidencePanel
      v-if="evidence && attempt"
      :source="evidence"
      :sources="attempt.sources"
      @select="evidence = $event"
      @close="evidence = null"
    />
  </main>
</template>
<style scoped>
.attempt-history {
  max-width: 1000px;
}
.quiz-card {
  margin-top: var(--space-6);
}
.saved-options {
  padding-left: var(--space-5);
}
.saved-options li {
  padding: var(--space-3);
  border-bottom: 1px solid var(--color-line);
  overflow-wrap: anywhere;
}
.saved-options strong {
  display: inline-block;
  margin-left: var(--space-3);
  color: var(--color-accent);
  font-size: var(--text-sm);
}
</style>
