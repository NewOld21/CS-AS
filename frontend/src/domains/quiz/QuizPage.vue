<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuth } from '../auth/store'
import { errorMessage } from '../auth/validation'
import { ApiError } from '../../shared/api/client'
import SafeAnswer from '../chat/SafeAnswer.vue'
import EvidencePanel from '../chat/EvidencePanel.vue'
import BaseButton from '../../shared/ui/BaseButton.vue'
import StatusMessage from '../../shared/ui/StatusMessage.vue'
import {
  ask,
  createContextChat,
  createGeneralChat,
  getChatMessages,
  getQuiz,
  generateQuiz,
  recoverGeneration,
  listChatSessions,
  listCategories,
  listQuizzes,
  submitAttempt,
  type Attempt,
  type Category,
  type ChatAnswer,
  type ChatSession,
  type Quiz,
  type Source,
} from './api'

const auth = useAuth()
const router = useRouter()
const route = useRoute()
const pendingAttempt = ref<{ key: string; option: string } | null>(null)
function attemptStorageKey() {
  return `csas:attempt:${auth.user?.id}:${quiz.value?.id}:${route.query.retry_of_attempt_id ?? ''}`
}
const categories = ref<Category[]>([])
const category = ref('')
const quizzes = ref<Quiz[]>([])
const index = ref(0)
const selected = ref('')
const result = ref<Attempt | null>(null)
const loading = ref(true)
const busy = ref(false)
const failure = ref('')
const chatOpen = ref(false)
const chatSession = ref('')
const chatQuestion = ref('왜 틀렸어?')
const chatBusy = ref(false)
const chatFailure = ref('')
const generating = ref(false)
const generationNotice = ref('')
function generationKey() {
  return `csas:generation:${auth.user?.id}:${chatSession.value}`
}
function showGenerated(response: import('./api').GenerationResult) {
  if (response.status === 'ready' && response.quiz) {
    quizzes.value = [
      response.quiz,
      ...quizzes.value.filter((item) => item.id !== response.quiz!.id),
    ]
    index.value = 0
    selected.value = ''
    result.value = null
    generationNotice.value = '검증 단계를 통과한 AI 생성 문제입니다. 답안을 제출해 확인해 보세요.'
  } else {
    generationNotice.value =
      response.status === 'insufficient_evidence'
        ? '문제를 만들 근거가 부족합니다.'
        : '문제 검증을 통과하지 못했습니다. 후보는 공개하지 않습니다.'
  }
}
async function generateRelated() {
  if (!chatSession.value || generating.value) return
  generating.value = true
  generationNotice.value = ''
  const pending = sessionStorage.getItem(generationKey())
  const key = pending || crypto.randomUUID()
  sessionStorage.setItem(generationKey(), key)
  const recent = [...messages.value].reverse().find((item) => item.answer?.concept_ids.length)
  try {
    let response
    if (pending) {
      try {
        response = await recoverGeneration(key)
      } catch (error) {
        if (!(error instanceof ApiError) || error.status !== 404) throw error
      }
    }
    response ??= await generateQuiz(recent?.answer?.concept_ids ?? [], chatSession.value, key)
    showGenerated(response)
    sessionStorage.setItem(generationKey() + ':last', key)
    sessionStorage.removeItem(generationKey())
  } catch (error) {
    if (
      error instanceof ApiError &&
      [
        'GENERATION_FAILED',
        'RAG_TIMEOUT',
        'RAG_UNAVAILABLE',
        'RAG_FAILED',
        'GENERATION_SAVE_FAILED',
        'GENERATION_INVALID',
        'DUPLICATE_GENERATED_QUIZ',
      ].includes(error.code)
    )
      sessionStorage.removeItem(generationKey())
    generationNotice.value =
      errorMessage(error) + ' 같은 요청은 다시 확인하며 중복 생성하지 않습니다.'
  } finally {
    generating.value = false
  }
}
const chatSessions = ref<ChatSession[]>([])
const messages = ref<
  Array<{
    role: 'user' | 'assistant'
    text: string
    status?: 'pending' | 'answered' | 'insufficient_evidence' | 'failed' | null
    answer?: ChatAnswer
  }>
>([])
const evidence = ref<Source | null>(null)
const evidenceSources = ref<Source[]>([])
function showEvidence(source: Source, sources: Source[]) {
  evidence.value = source
  evidenceSources.value = sources
}
const quiz = computed(() => quizzes.value[index.value] ?? null)

async function start() {
  loading.value = true
  failure.value = ''
  try {
    await auth.restore()
    if (!auth.user) {
      await router.replace('/login')
      return
    }
    categories.value = await listCategories()
    if (typeof route.query.quiz_id === 'string') {
      quizzes.value = [await getQuiz(route.query.quiz_id)]
      resetQuestion()
    } else if (categories.value.length) await chooseCategory(categories.value[0]!.id)
    if (typeof route.query.chat_session_id === 'string') {
      await loadSessions()
      const session = chatSessions.value.find((item) => item.id === route.query.chat_session_id)
      if (session) {
        chatOpen.value = true
        await selectChat(session)
      }
    }
  } catch (error) {
    failure.value = errorMessage(error)
  } finally {
    loading.value = false
  }
}
async function chooseCategory(value: string) {
  category.value = value
  failure.value = ''
  const page = await listQuizzes(value)
  quizzes.value = page.items
  index.value = 0
  resetQuestion()
}
function resetQuestion() {
  pendingAttempt.value = null
  selected.value = ''
  result.value = null
  chatOpen.value = false
  chatSession.value = ''
  messages.value = []
  const saved = sessionStorage.getItem(attemptStorageKey())
  if (saved) {
    try {
      const value = JSON.parse(saved)
      if (
        typeof value.key === 'string' &&
        quiz.value?.options.some((option) => option.id === value.option)
      ) {
        pendingAttempt.value = value
        selected.value = value.option
      } else sessionStorage.removeItem(attemptStorageKey())
    } catch {
      sessionStorage.removeItem(attemptStorageKey())
    }
  }
}
async function submit() {
  if (!quiz.value || !selected.value || busy.value) return
  busy.value = true
  failure.value = ''
  try {
    pendingAttempt.value ??= { key: crypto.randomUUID(), option: selected.value }
    sessionStorage.setItem(attemptStorageKey(), JSON.stringify(pendingAttempt.value))
    result.value = await submitAttempt(
      quiz.value.id,
      pendingAttempt.value.option,
      pendingAttempt.value.key,
      quiz.value.id === route.query.quiz_id && typeof route.query.retry_of_attempt_id === 'string'
        ? route.query.retry_of_attempt_id
        : undefined,
    )
    sessionStorage.removeItem(attemptStorageKey())
    pendingAttempt.value = null
  } catch (error) {
    failure.value = errorMessage(error)
  } finally {
    busy.value = false
  }
}
async function openChat() {
  if (!quiz.value || !result.value) return
  chatOpen.value = true
  chatFailure.value = ''
  try {
    await loadSessions()
    const existing = chatSessions.value.find((session) => session.attempt_id === result.value?.id)
    if (existing) await selectChat(existing)
    else await selectChat(await createContextChat(quiz.value.id, result.value.id))
    await loadSessions()
  } catch (error) {
    chatFailure.value = errorMessage(error)
  }
}
async function openHistory() {
  chatOpen.value = true
  chatFailure.value = ''
  try {
    await loadSessions()
    if (chatSessions.value[0]) await selectChat(chatSessions.value[0])
  } catch (error) {
    chatFailure.value = errorMessage(error)
  }
}
async function loadSessions() {
  chatSessions.value = (await listChatSessions()).items
}
async function selectChat(session: ChatSession) {
  chatSession.value = session.id
  const saved = (await getChatMessages(session.id)).items
  messages.value = saved.map((message) => ({
    role: message.role === 'USER' ? 'user' : 'assistant',
    text:
      message.content ??
      (message.status === 'failed'
        ? '답변 생성에 실패했습니다. 같은 질문을 다시 보내 주세요.'
        : '답변을 생성하고 있습니다.'),
    status: message.status,
    answer:
      message.role === 'ASSISTANT'
        ? {
            request_id: message.request_id ?? '',
            message_id: message.id,
            status:
              message.status === 'insufficient_evidence' ? 'insufficient_evidence' : 'answered',
            answer: message.content,
            sources: message.sources,
            concept_ids: message.concept_ids,
          }
        : undefined,
  }))
  const pending =
    sessionStorage.getItem(generationKey()) || sessionStorage.getItem(generationKey() + ':last')
  if (pending) {
    try {
      showGenerated(await recoverGeneration(pending))
      sessionStorage.removeItem(generationKey())
    } catch {
      generationNotice.value =
        '이전 생성 요청을 확인 중입니다. 같은 요청으로 다시 확인할 수 있습니다.'
    }
  }
}
async function newGeneralChat() {
  chatFailure.value = ''
  try {
    await selectChat(await createGeneralChat())
    await loadSessions()
  } catch (error) {
    chatFailure.value = errorMessage(error)
  }
}
async function sendQuestion() {
  const question = chatQuestion.value.trim()
  if (!chatSession.value || !question || chatBusy.value) return
  messages.value.push({ role: 'user', text: question })
  chatQuestion.value = ''
  chatBusy.value = true
  chatFailure.value = ''
  try {
    const response = await ask(chatSession.value, question)
    messages.value.push({
      role: 'assistant',
      text: response.answer ?? '현재 확보된 CS 문서에서 답할 충분한 근거를 찾지 못했습니다.',
      answer: response,
    })
  } catch (error) {
    chatFailure.value = errorMessage(error)
    try {
      const session = chatSessions.value.find((item) => item.id === chatSession.value)
      if (session) await selectChat(session)
    } catch {
      // Keep the original provider/persistence error visible.
    }
  } finally {
    chatBusy.value = false
    await loadSessions().catch(() => undefined)
  }
}
function next() {
  index.value = (index.value + 1) % quizzes.value.length
  resetQuestion()
}
onMounted(start)
</script>

<template>
  <main id="main" class="learn-page" tabindex="-1">
    <header class="learn-heading">
      <div>
        <p class="eyebrow">CHECK · ASK · CONNECT</p>
        <h1>한 문제에서, 더 깊은 이해로.</h1>
      </div>
      <p>답을 고르고 서버 채점을 확인한 뒤, 현재 풀이를 아는 AS에게 바로 질문하세요.</p>
    </header>
    <div v-if="loading" class="learn-state" role="status">
      <span class="spinner"></span>학습 공간을 준비하고 있어요.
    </div>
    <StatusMessage v-else-if="failure && !quiz" kind="error">{{ failure }}</StatusMessage>
    <template v-else>
      <nav v-if="!route.query.quiz_id" class="category-tabs" aria-label="CS 분야 선택">
        <button
          v-for="item in categories"
          :key="item.id"
          :class="{ active: category === item.id }"
          @click="chooseCategory(item.id)"
        >
          {{ item.name }} <span>{{ item.quiz_count }}</span>
        </button>
      </nav>
      <section v-if="quiz" class="learning-layout">
        <article class="quiz-card" aria-labelledby="quiz-stem">
          <div class="quiz-meta">
            <span v-if="quiz.origin === 'AI_GENERATED'">AI 생성 문제 · 개인 학습</span>
            <span class="mono">Q {{ index + 1 }} / {{ quizzes.length }}</span
            ><span>{{ quiz.difficulty }}</span>
          </div>
          <h2 id="quiz-stem">{{ quiz.stem }}</h2>
          <fieldset :disabled="busy || !!result || !!pendingAttempt">
            <legend class="sr-only">답안 선택</legend>
            <label
              v-for="option in quiz.options"
              :key="option.id"
              :class="[
                'quiz-option',
                {
                  selected: selected === option.id,
                  correct: result?.correct_option_id === option.id,
                  wrong: result && selected === option.id && !result.is_correct,
                },
              ]"
            >
              <input v-model="selected" type="radio" name="answer" :value="option.id" />
              <span class="option-index mono">{{ String.fromCharCode(65 + option.position) }}</span
              ><span>{{ option.text }}</span>
            </label>
          </fieldset>
          <StatusMessage v-if="failure" kind="error">{{ failure }}</StatusMessage>
          <div
            v-if="result"
            class="attempt-feedback"
            :class="result.is_correct ? 'is-correct' : 'is-wrong'"
            role="status"
          >
            <strong>{{ result.is_correct ? '정답이에요.' : '다시 연결해 볼 지점이에요.' }}</strong>
            <p>{{ result.explanation }}</p>
            <button
              v-for="source in result.sources"
              :key="source.chunk_id"
              type="button"
              @click="showEvidence(source, result.sources)"
            >
              {{ source.title }} · 생성 근거 보기
            </button>
          </div>
          <div class="quiz-actions">
            <BaseButton variant="secondary" @click="openHistory">이전 대화</BaseButton>
            <BaseButton v-if="!result" :disabled="!selected" :loading="busy" @click="submit">{{
              pendingAttempt ? '제출 결과 다시 확인' : '답안 제출'
            }}</BaseButton>
            <template v-else
              ><BaseButton @click="openChat">AS에게 질문하기</BaseButton
              ><BaseButton v-if="!route.query.quiz_id" variant="secondary" @click="next"
                >다음 문제</BaseButton
              ><RouterLink v-else to="/me/wrong-answers">오답노트 확인</RouterLink></template
            >
          </div>
        </article>
        <aside v-if="chatOpen" class="chat-panel" aria-labelledby="chat-title">
          <div class="chat-title">
            <div>
              <span class="eyebrow">CONTEXTUAL AS</span>
              <h2 id="chat-title">이 풀이에 대해 질문하기</h2>
            </div>
            <button aria-label="채팅 닫기" @click="chatOpen = false">×</button>
          </div>
          <p class="chat-context">
            퀴즈 대화의 문제와 선택한 답은 서버가 풀이 기록에서 안전하게 복원합니다.
          </p>
          <nav class="chat-history" aria-label="이전 대화">
            <div class="chat-history-heading">
              <strong>내 대화</strong>
              <button type="button" @click="newGeneralChat">새 일반 대화</button>
            </div>
            <button
              v-for="session in chatSessions"
              :key="session.id"
              type="button"
              :class="{ active: chatSession === session.id }"
              @click="selectChat(session)"
            >
              <span>{{ session.title }}</span>
              <small>{{ session.attempt_id ? '퀴즈 AS' : '일반 질문' }}</small>
            </button>
          </nav>
          <div class="message-list" aria-live="polite">
            <div v-if="!messages.length" class="chat-empty">
              “왜 틀렸어?”처럼 짧게 물어도 지금 문제의 문맥과 함께 검색해요.
            </div>
            <article
              v-for="(message, messageIndex) in messages"
              :key="messageIndex"
              :class="['message', message.role, { failed: message.status === 'failed' }]"
            >
              <span class="mono">{{ message.role === 'user' ? 'YOU' : 'AS' }}</span
              ><SafeAnswer
                :content="message.text"
                :sources="message.answer?.sources"
                @evidence="showEvidence($event, message.answer!.sources)"
              />
              <ul v-if="message.answer?.sources.length" class="source-list">
                <li v-for="source in message.answer.sources" :key="source.chunk_id">
                  <button type="button" @click="showEvidence(source, message.answer!.sources)">
                    {{ source.title }} · 근거 보기
                  </button>
                </li>
              </ul>
            </article>
            <div v-if="chatBusy" class="message assistant" role="status">
              <span class="spinner"></span>근거 문서를 찾고 있어요.
            </div>
          </div>
          <StatusMessage v-if="chatFailure" kind="error">{{ chatFailure }}</StatusMessage>
          <StatusMessage v-if="generationNotice">{{ generationNotice }}</StatusMessage>
          <BaseButton
            v-if="messages.some((item) => item.answer?.status === 'answered')"
            :disabled="chatBusy || generating"
            :loading="generating"
            @click="generateRelated"
            >관련 퀴즈 만들기</BaseButton
          >
          <form class="chat-form" @submit.prevent="sendQuestion">
            <label for="chat-question" class="sr-only">AS 질문</label
            ><textarea
              id="chat-question"
              v-model="chatQuestion"
              maxlength="2000"
              rows="3"
              placeholder="이 선택지는 왜 정답이 아니야?"
            ></textarea
            ><BaseButton
              type="submit"
              :disabled="!chatSession || !chatQuestion.trim()"
              :loading="chatBusy"
              >질문 보내기</BaseButton
            >
          </form>
        </aside>
      </section>
      <div v-else class="learn-state">이 분야에 학습 가능한 문제가 아직 없습니다.</div>
    </template>
    <EvidencePanel
      v-if="evidence"
      :source="evidence"
      :sources="evidenceSources"
      @select="evidence = $event"
      @close="evidence = null"
    />
  </main>
</template>
