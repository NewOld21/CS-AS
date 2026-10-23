<script setup lang="ts">
import { computed, nextTick, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuth } from '../auth/store'
import { errorMessage } from '../auth/validation'
import { ApiError, request } from '../../shared/api/client'
import {
  ask,
  createGeneralChat,
  getChatMessages,
  listChatSessions,
  type ChatMessage,
  type ChatSession,
  type Source,
} from '../quiz/api'
import BaseButton from '../../shared/ui/BaseButton.vue'
import StatusMessage from '../../shared/ui/StatusMessage.vue'
import SafeAnswer from './SafeAnswer.vue'
import EvidencePanel from './EvidencePanel.vue'

const auth = useAuth()
const route = useRoute()
const router = useRouter()
const sessions = ref<ChatSession[]>([])
const selected = ref('')
const messages = ref<ChatMessage[]>([])
const question = ref('')
const loading = ref(true)
const busy = ref(false)
const failure = ref('')
const nextSessionPage = ref<number | null>(null)
const nextMessagePage = ref<number | null>(null)
const evidence = ref<Source | null>(null)
const evidenceSources = ref<Source[]>([])
const runtime = ref<{
  mode: string
  model: string
  live: boolean
  corpus_kind: string
  configured: boolean
  error_code?: string
} | null>(null)
const log = ref<HTMLElement>()
const input = ref<HTMLTextAreaElement>()
const current = computed(() => sessions.value.find((s) => s.id === selected.value))
const suggestions = [
  '프로세스와 스레드의 차이는?',
  'TCP 3-way handshake를 설명해줘.',
  '트랜잭션 격리 수준은 왜 필요해?',
]
let loadId = 0
function pendingKey() {
  return `csas:chat:${auth.user?.id}:${selected.value}`
}
async function scroll() {
  await nextTick()
  log.value?.scrollTo({ top: log.value.scrollHeight, behavior: 'instant' })
}
async function failed(error: unknown) {
  if (error instanceof ApiError && error.status === 401) {
    auth.user = null
    await router.replace('/login')
  }
  failure.value = errorMessage(error)
}
async function loadSessions(page = 0) {
  const result = await listChatSessions(page)
  sessions.value = page ? [...sessions.value, ...result.items] : result.items
  nextSessionPage.value = result.next_page
}
async function choose(id: string) {
  if (busy.value) return
  const token = ++loadId
  selected.value = id
  messages.value = []
  failure.value = ''
  loading.value = true
  question.value = ''
  evidence.value = null
  await router.replace({ path: '/chat', query: { session: id } })
  try {
    const page = await getChatMessages(id)
    if (token !== loadId) return
    messages.value = page.items
    nextMessagePage.value = page.next_page
    await scroll()
  } catch (error) {
    if (token === loadId) await failed(error)
  } finally {
    if (token === loadId) loading.value = false
  }
}
async function moreMessages() {
  if (nextMessagePage.value === null || busy.value) return
  busy.value = true
  try {
    const result = await getChatMessages(selected.value, nextMessagePage.value)
    messages.value.push(...result.items)
    nextMessagePage.value = result.next_page
    await scroll()
  } catch (error) {
    await failed(error)
  } finally {
    busy.value = false
  }
}
async function newChat() {
  if (busy.value) return
  failure.value = ''
  try {
    const session = await createGeneralChat('CS 자유 학습')
    await loadSessions()
    await choose(session.id)
    input.value?.focus()
  } catch (error) {
    await failed(error)
  }
}
async function send() {
  if (busy.value || !question.value.trim() || question.value.length > 2000) return
  const content = question.value.trim()
  if (!selected.value) {
    await newChat()
    if (!selected.value) return
  }
  question.value = content
  busy.value = true
  failure.value = ''
  let key = crypto.randomUUID()
  const saved = sessionStorage.getItem(pendingKey())
  if (saved) {
    try {
      const pending = JSON.parse(saved)
      if (pending.question === content && typeof pending.key === 'string') key = pending.key
    } catch {
      sessionStorage.removeItem(pendingKey())
    }
  }
  sessionStorage.setItem(pendingKey(), JSON.stringify({ key, question: content }))
  try {
    await ask(selected.value, content, key)
    sessionStorage.removeItem(pendingKey())
    question.value = ''
    // Read the server-owned transcript, including a recovered prior request; never append a duplicate.
    const result = await getChatMessages(selected.value)
    messages.value = result.items
    nextMessagePage.value = result.next_page
    await loadSessions()
    await scroll()
  } catch (error) {
    await failed(error)
  } finally {
    busy.value = false
    input.value?.focus()
  }
}
function recommend(value: string) {
  question.value = value
  input.value?.focus()
}
function enter(event: KeyboardEvent) {
  if (!event.shiftKey && !event.isComposing) {
    event.preventDefault()
    void send()
  }
}
function show(source: Source, sources: Source[]) {
  evidence.value = source
  evidenceSources.value = sources
}
function sourceKind(source: Source) {
  if (source.source_id.includes('wikipedia')) return 'Wikipedia'
  if (/github\.com/.test(source.url)) return 'GitHub'
  if (source.source_id === 'local-demo') return '개발 예제'
  return '외부 기술 문서'
}
onMounted(async () => {
  try {
    await auth.restore()
    if (!auth.user) {
      await router.replace('/login')
      return
    }
    await loadSessions()
    try {
      runtime.value = await request('/chat/status')
    } catch {
      runtime.value = null
    }
    if (typeof route.query.session === 'string') await choose(route.query.session)
  } catch (error) {
    await failed(error)
  } finally {
    loading.value = false
  }
})
</script>
<template>
  <main id="main" class="chat-workspace" tabindex="-1">
    <header class="chat-intro">
      <div>
        <p class="eyebrow">ASK · UNDERSTAND · CONNECT</p>
        <h1>궁금함에서 시작하는 CS.</h1>
      </div>
      <RouterLink to="/learn">CS 퀴즈 풀기 ↗</RouterLink>
    </header>
    <StatusMessage v-if="runtime && !runtime.configured" kind="error">{{
      runtime.error_code === 'GMS_KEY_MISSING'
        ? 'GMS 키가 설정되지 않았습니다.'
        : 'CS 검색 인덱스가 준비되지 않았습니다.'
    }}</StatusMessage>
    <StatusMessage v-else-if="runtime && !runtime.live" kind="info"
      >개발 예제 모드입니다. 실제 GMS 답변이 아닙니다.</StatusMessage
    >
    <StatusMessage v-else-if="!runtime && !loading" kind="info"
      >AI 연결 상태를 확인하지 못했습니다. 질문 시 연결 오류를 안내합니다.</StatusMessage
    >
    <p v-else-if="runtime" class="muted">
      {{ runtime.model }} ·
      {{ runtime.corpus_kind === 'active' ? '검색 인덱스' : '개발 예제 문서 인덱스' }} 기반
    </p>
    <div class="chat-grid">
      <aside class="conversation-list" aria-label="대화 기록">
        <BaseButton :disabled="busy" @click="newChat">새 대화</BaseButton>
        <h2>나의 대화</h2>
        <p v-if="!sessions.length">첫 질문을 시작해 보세요.</p>
        <button
          v-for="session in sessions"
          :key="session.id"
          type="button"
          :disabled="busy"
          :aria-pressed="selected === session.id"
          @click="choose(session.id)"
        >
          <strong>{{ session.title }}</strong
          ><span>{{ session.attempt_id ? '퀴즈 AS' : 'CS 자유 학습' }}</span></button
        ><BaseButton
          v-if="nextSessionPage !== null"
          variant="secondary"
          :disabled="busy"
          @click="loadSessions(nextSessionPage!)"
          >대화 더 보기</BaseButton
        >
      </aside>
      <section class="conversation" aria-label="CS 학습 대화">
        <h2>{{ current?.title || '어떤 개념을 알아볼까요?' }}</h2>
        <p v-if="current?.attempt_id" class="muted">
          이 대화는 저장된 퀴즈 풀이 문맥을 사용합니다.
        </p>
        <div
          ref="log"
          class="conversation-log"
          role="log"
          aria-label="질문과 답변"
          :aria-busy="busy"
        >
          <p v-if="loading" role="status">대화를 불러오고 있어요.</p>
          <div v-else-if="!messages.length" class="chat-welcome">
            <p>퀴즈 없이도 질문할 수 있어요. 이어지는 질문은 이 대화의 문맥으로 검색합니다.</p>
            <button
              v-for="suggestion in suggestions"
              :key="suggestion"
              type="button"
              @click="recommend(suggestion)"
            >
              {{ suggestion }}
            </button>
          </div>
          <article
            v-for="message in messages"
            :key="message.id"
            :class="['conversation-message', message.role === 'USER' ? 'from-user' : 'from-as']"
          >
            <h3>{{ message.role === 'USER' ? '나' : 'AS' }}</h3>
            <p v-if="message.role === 'USER'">{{ message.content }}</p>
            <template v-else
              ><p v-if="message.status === 'failed'">
                답변을 완료하지 못했습니다. 질문을 다시 보내 주세요.
              </p>
              <p v-else-if="message.status === 'pending'" role="status">
                이 질문의 답변을 처리하고 있습니다. 잠시 후 대화를 다시 선택해 확인하세요.
              </p>
              <p v-else-if="message.status === 'insufficient_evidence'">
                현재 확보된 CS 문서에서는 답할 충분한 근거를 확인하지 못했습니다.
              </p>
              <SafeAnswer
                v-else
                :content="message.content || ''"
                :sources="message.sources"
                @evidence="show($event, message.sources)"
              />
              <p v-if="!message.sources.length && message.status !== 'pending'" class="muted">
                확인된 근거 문서가 없습니다.
              </p>
              <div v-else class="chat-sources" aria-label="답변 근거">
                <button
                  v-for="(source, i) in message.sources"
                  :key="source.chunk_id"
                  type="button"
                  @click="show(source, message.sources)"
                >
                  [{{ i + 1 }}] {{ source.title }}
                  <span>{{ sourceKind(source) }} · {{ source.locator }}</span>
                </button>
              </div>
            </template>
          </article>
          <p v-if="busy" role="status">
            질문을 처리하고 있습니다. 검색 근거를 확인한 답변을 기다려 주세요.
          </p>
          <BaseButton
            v-if="nextMessagePage !== null"
            variant="secondary"
            :disabled="busy"
            @click="moreMessages"
            >다음 대화 불러오기</BaseButton
          >
        </div>
        <StatusMessage v-if="failure" kind="error">{{ failure }}</StatusMessage>
        <form class="chat-composer" @submit.prevent="send">
          <label for="cs-question">CS 질문</label
          ><textarea
            id="cs-question"
            ref="input"
            v-model="question"
            :disabled="busy"
            maxlength="2000"
            rows="3"
            placeholder="개념, 비교, 코드 예시를 물어보세요."
            @keydown.enter="enter"
          />
          <div>
            <span class="muted">Enter 전송 · Shift+Enter 줄바꿈</span
            ><BaseButton type="submit" :disabled="busy || !question.trim()" :loading="busy"
              >질문 보내기</BaseButton
            >
          </div>
        </form>
      </section>
    </div>
    <EvidencePanel
      v-if="evidence"
      :source="evidence"
      :sources="evidenceSources"
      @select="evidence = $event"
      @close="evidence = null"
    />
  </main>
</template>
<style scoped>
.chat-workspace {
  padding: var(--space-7) var(--page-gutter);
  max-width: var(--page-width);
  margin: auto;
}
.chat-intro {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-4);
  margin-bottom: var(--space-5);
}
.chat-intro h1 {
  font-size: var(--text-2xl);
}
.chat-grid {
  display: grid;
  grid-template-columns: 240px minmax(0, 1fr);
  gap: var(--space-5);
  margin-top: var(--space-5);
}
.conversation-list,
.conversation {
  padding: var(--space-5);
  border: 1px solid var(--color-line);
  border-radius: var(--radius-md);
  background: var(--color-panel);
  min-width: 0;
}
.conversation-list > button {
  width: 100%;
  margin-bottom: var(--space-3);
}
.conversation-list > button:not(.button) {
  display: grid;
  text-align: left;
  padding: var(--space-3);
  background: var(--color-bg);
  border: 1px solid var(--color-line);
  border-radius: var(--radius-sm);
  color: var(--color-ink);
  gap: var(--space-2);
  overflow-wrap: anywhere;
}
.conversation-list button[aria-pressed='true'] {
  border-color: var(--color-accent);
}
.conversation-list span {
  color: var(--color-muted);
}
.conversation-log {
  max-height: 65vh;
  min-height: 260px;
  overflow-y: auto;
  padding: var(--space-2);
}
.conversation-message {
  padding: var(--space-4);
  margin-block: var(--space-4);
  border-radius: var(--radius-md);
  overflow-wrap: anywhere;
}
.from-user {
  background: var(--color-panel-raised);
}
.from-user p {
  white-space: pre-wrap;
}
.from-as {
  border: 1px solid var(--color-line-soft);
}
.conversation-message h3 {
  font-size: var(--text-sm);
  color: var(--color-accent);
}
.chat-welcome button,
.chat-sources button {
  display: block;
  text-align: left;
  max-width: 100%;
  padding: var(--space-3);
  margin-block: var(--space-2);
  color: var(--color-blue);
  background: transparent;
  border: 1px solid var(--color-line);
  border-radius: var(--radius-sm);
  overflow-wrap: anywhere;
}
.chat-sources span {
  display: block;
  font-size: var(--text-sm);
  color: var(--color-muted);
}
.chat-composer {
  border-top: 1px solid var(--color-line);
  padding-top: var(--space-4);
}
.chat-composer label {
  display: block;
  margin-bottom: var(--space-2);
}
.chat-composer textarea {
  width: 100%;
  resize: vertical;
  min-height: 90px;
  padding: var(--space-3);
  font: inherit;
  color: var(--color-ink);
  background: var(--color-bg);
  border: 1px solid var(--color-line);
  border-radius: var(--radius-sm);
}
.chat-composer > div {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-3);
  justify-content: space-between;
  align-items: center;
  margin-top: var(--space-3);
}
@media (max-width: 760px) {
  .chat-grid {
    grid-template-columns: minmax(0, 1fr);
  }
  .conversation-list {
    max-height: 240px;
    overflow-y: auto;
  }
  .conversation-log {
    max-height: 60vh;
  }
  .chat-workspace {
    padding-inline: var(--space-4);
  }
}
</style>
