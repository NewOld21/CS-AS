<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuth } from '../auth/store'
import { errorMessage } from '../auth/validation'
import { ApiError } from '../../shared/api/client'
import BaseButton from '../../shared/ui/BaseButton.vue'
import StatusMessage from '../../shared/ui/StatusMessage.vue'
import {
  categoryLabels,
  getHistory,
  getReviews,
  getStats,
  percentage,
  timestamp,
  type Page,
  type ReviewItem,
  type Stats,
} from './api'
import type { Attempt } from '../quiz/api'

const auth = useAuth()
const route = useRoute()
const router = useRouter()
const isReview = computed(() => route.path === '/me/wrong-answers')
const category = ref(typeof route.query.category === 'string' ? route.query.category : '')
const origin = ref(typeof route.query.origin === 'string' ? route.query.origin : '')
const correct = ref(typeof route.query.correct === 'string' ? route.query.correct : '')
const status = ref(typeof route.query.status === 'string' ? route.query.status : '')
const stats = ref<Stats | null>(null)
const statsFailure = ref('')
const failure = ref('')
const loading = ref(true)
const statsLoading = ref(true)
const history = ref<Page<Attempt>>({ items: [], next_cursor: null, total_count: 0 })
const reviews = ref<Page<ReviewItem>>({ items: [], next_cursor: null, total_count: 0 })
const cursors = ref<Array<string | null>>([null])
const page = ref(0)
let sequence = 0
const pageInfo = computed(() => (isReview.value ? reviews.value : history.value))
const rows = computed(() =>
  isReview.value
    ? reviews.value.items.map((item) => ({
        id: item.latest_attempt_id,
        quiz: item.quiz,
        state: item.status === 'RESOLVED' ? '해결' : '복습 필요',
        at: item.last_wrong_at,
        wrongs: item.wrong_attempts,
        retryable: item.retryable,
      }))
    : history.value.items.map((item) => ({
        id: item.id,
        quiz: item.quiz,
        state: item.is_correct ? '정답' : '오답',
        at: item.submitted_at,
        wrongs: null,
        retryable: false,
      })),
)

async function handle(error: unknown) {
  if (error instanceof ApiError && error.status === 401) {
    auth.user = null
    await router.replace('/login')
  }
  return errorMessage(error)
}
async function loadStats() {
  statsLoading.value = true
  statsFailure.value = ''
  try {
    stats.value = await getStats()
  } catch (error) {
    statsFailure.value = await handle(error)
  } finally {
    statsLoading.value = false
  }
}
async function loadPage() {
  const current = ++sequence
  loading.value = true
  failure.value = ''
  try {
    const filters = {
      category: category.value,
      origin: origin.value,
      limit: '10',
      cursor: cursors.value[page.value],
      ...(isReview.value ? { status: status.value } : { correct: correct.value }),
    }
    if (isReview.value) {
      const result = await getReviews(filters)
      if (current === sequence) reviews.value = result
    } else {
      const result = await getHistory(filters)
      if (current === sequence) history.value = result
    }
  } catch (error) {
    if (current === sequence) failure.value = await handle(error)
  } finally {
    if (current === sequence) loading.value = false
  }
}
async function filtersChanged() {
  cursors.value = [null]
  page.value = 0
  await router.replace({
    path: route.path,
    query: {
      ...(category.value ? { category: category.value } : {}),
      ...(origin.value ? { origin: origin.value } : {}),
      ...(correct.value && !isReview.value ? { correct: correct.value } : {}),
      ...(status.value && isReview.value ? { status: status.value } : {}),
    },
  })
  await loadPage()
}
async function next() {
  if (!pageInfo.value.next_cursor || loading.value) return
  cursors.value = [...cursors.value.slice(0, page.value + 1), pageInfo.value.next_cursor]
  page.value++
  await loadPage()
}
async function previous() {
  if (page.value > 0 && !loading.value) {
    page.value--
    await loadPage()
  }
}
watch([category, origin, correct, status], filtersChanged)
onMounted(async () => {
  try {
    await auth.restore()
    if (!auth.user) {
      await router.replace('/login')
      return
    }
    await Promise.all([loadStats(), loadPage()])
  } catch (error) {
    failure.value = await handle(error)
    loading.value = false
    statsLoading.value = false
  }
})
</script>

<template>
  <main id="main" class="account-page learning-dashboard" tabindex="-1">
    <p class="eyebrow">YOUR LEARNING ORBIT</p>
    <h1>{{ isReview ? '다시 연결하는 오답노트.' : '나의 학습 궤적.' }}</h1>
    <p>일반 문제와 AI 생성 문제의 모든 풀이를 함께 보관합니다. 정답률에는 재풀이도 포함됩니다.</p>
    <nav class="learning-tabs" aria-label="학습 기록 메뉴">
      <RouterLink to="/me">풀이 이력 · 통계</RouterLink
      ><RouterLink to="/me/wrong-answers">오답노트</RouterLink
      ><RouterLink to="/learn">퀴즈 풀기</RouterLink>
    </nav>
    <p v-if="statsLoading" role="status">학습 통계를 불러오고 있어요.</p>
    <div v-else-if="statsFailure">
      <StatusMessage kind="error">{{ statsFailure }}</StatusMessage
      ><BaseButton variant="secondary" @click="loadStats">통계 다시 불러오기</BaseButton>
    </div>
    <section v-else-if="stats" aria-label="학습 통계" class="learning-stats">
      <article>
        <span>총 풀이</span><strong>{{ stats.total_attempts }}</strong>
      </article>
      <article>
        <span>맞힌 풀이</span><strong>{{ stats.correct_attempts }}</strong>
      </article>
      <article>
        <span>정답률</span><strong>{{ percentage(stats.accuracy) }}</strong>
      </article>
      <article>
        <span>서로 다른 문제</span><strong>{{ stats.unique_quizzes }}</strong>
      </article>
      <article>
        <span>복습 필요</span><strong>{{ stats.needs_review }}</strong>
      </article>
      <article>
        <span>해결한 오답</span><strong>{{ stats.resolved_reviews }}</strong>
      </article>
    </section>
    <section
      v-if="stats && !statsFailure && !isReview"
      class="category-stats"
      aria-label="분야별 정답률"
    >
      <h2>분야별 정답률</h2>
      <p v-if="!stats.by_category.length">아직 분야별 학습 기록이 없습니다.</p>
      <div v-for="item in stats.by_category" :key="item.category">
        <span>{{ categoryLabels[item.category] || item.category }}</span
        ><meter
          :value="item.accuracy ?? 0"
          min="0"
          max="1"
          :aria-label="`${categoryLabels[item.category]} 정답률`"
        /><span
          >{{ percentage(item.accuracy) }} · {{ item.correct_attempts }} /
          {{ item.total_attempts }}회</span
        >
      </div>
    </section>
    <section class="learning-records" :aria-label="isReview ? '오답 목록' : '풀이 이력'">
      <h2>{{ isReview ? '문제별 복습 상태' : '모든 풀이 기록' }}</h2>
      <div class="learning-filters">
        <label
          >분야<select v-model="category">
            <option value="">전체 분야</option>
            <option v-for="(label, id) in categoryLabels" :key="id" :value="id">{{ label }}</option>
          </select></label
        >
        <label
          >문제 유형<select v-model="origin">
            <option value="">전체 유형</option>
            <option value="CURATED">일반 문제</option>
            <option value="AI_GENERATED">AI 생성 문제</option>
          </select></label
        >
        <label v-if="isReview"
          >복습 상태<select v-model="status">
            <option value="">전체 상태</option>
            <option value="NEEDS_REVIEW">복습 필요</option>
            <option value="RESOLVED">해결</option>
          </select></label
        >
        <label v-else
          >풀이 결과<select v-model="correct">
            <option value="">전체 결과</option>
            <option value="true">정답</option>
            <option value="false">오답</option>
          </select></label
        >
      </div>
      <p v-if="loading" role="status">기록을 불러오고 있어요.</p>
      <div v-else-if="failure">
        <StatusMessage kind="error">{{ failure }}</StatusMessage
        ><BaseButton variant="secondary" @click="loadPage">기록 다시 불러오기</BaseButton>
      </div>
      <template v-else>
        <p class="muted" aria-live="polite">필터에 맞는 기록 {{ pageInfo.total_count }}건</p>
        <div v-if="!rows.length" class="learn-state">
          <p>
            {{
              isReview ? '해당 조건의 오답 기록이 없습니다.' : '해당 조건의 풀이 기록이 없습니다.'
            }}
          </p>
          <RouterLink to="/learn">새 문제 풀러 가기 ↗</RouterLink>
        </div>
        <ol v-else class="learning-items">
          <li v-for="item in rows" :key="item.id">
            <div>
              <p class="record-meta">
                {{ categoryLabels[item.quiz.category] || item.quiz.category }} ·
                {{ item.quiz.difficulty }} ·
                {{ item.quiz.origin === 'AI_GENERATED' ? 'AI 생성 문제' : '일반 문제' }} · v{{
                  item.quiz.version
                }}
              </p>
              <h3>
                <RouterLink :to="`/me/attempts/${item.id}`">{{ item.quiz.stem }}</RouterLink>
              </h3>
              <p>
                {{ item.state }} <span v-if="item.wrongs !== null">· {{ item.wrongs }}회 오답</span>
              </p>
              <time :datetime="item.at">{{ timestamp(item.at) }}</time>
            </div>
            <RouterLink
              v-if="isReview && item.retryable"
              :to="{
                path: '/learn',
                query: { quiz_id: item.quiz.id, retry_of_attempt_id: item.id },
              }"
              class="button button--secondary"
              >다시 풀기</RouterLink
            ><span v-else-if="isReview" class="muted">이 버전은 재풀이할 수 없습니다.</span>
          </li>
        </ol>
        <nav class="learning-pagination" aria-label="기록 페이지">
          <BaseButton variant="secondary" :disabled="page === 0" @click="previous"
            >이전 페이지</BaseButton
          ><span>{{ page + 1 }} 페이지</span
          ><BaseButton variant="secondary" :disabled="!pageInfo.next_cursor" @click="next"
            >다음 페이지</BaseButton
          >
        </nav>
      </template>
    </section>
  </main>
</template>
<style scoped>
.learning-dashboard {
  max-width: 1120px;
}
.learning-tabs,
.learning-filters,
.learning-pagination {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-4);
  margin-block: var(--space-6);
  align-items: center;
}
.learning-tabs a {
  padding-block: var(--space-3);
  border-bottom: 2px solid var(--color-line);
}
.learning-tabs a.router-link-exact-active {
  border-color: var(--color-accent);
  color: var(--color-accent);
}
.learning-stats {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: var(--space-4);
}
.learning-stats article {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
  padding: var(--space-5);
  border: 1px solid var(--color-line);
  border-radius: var(--radius-md);
  background: var(--color-panel);
}
.learning-stats strong {
  font-size: var(--text-xl);
  color: var(--color-accent);
}
.category-stats,
.learning-records {
  margin-top: var(--space-7);
}
.category-stats > div {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-4);
  align-items: center;
  margin-block: var(--space-3);
}
meter {
  accent-color: var(--color-accent);
  flex: 1;
  min-width: 100px;
}
.learning-filters label {
  display: grid;
  gap: var(--space-2);
  flex: 1;
  min-width: 160px;
}
select {
  color: var(--color-ink);
  background: var(--color-panel);
  border: 1px solid var(--color-line);
  border-radius: var(--radius-sm);
  padding: var(--space-3);
  font: inherit;
  width: 100%;
}
.learning-items {
  list-style: none;
  padding: 0;
}
.learning-items li {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: var(--space-5);
  padding-block: var(--space-5);
  border-bottom: 1px solid var(--color-line);
}
.learning-items li > div {
  min-width: 0;
  overflow-wrap: anywhere;
}
.learning-items h3 {
  margin-block: var(--space-3);
}
.record-meta,
time {
  color: var(--color-muted);
  font-size: var(--text-sm);
}
.learning-pagination {
  justify-content: space-between;
}
@media (max-width: 600px) {
  .learning-stats {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
  .learning-stats article {
    padding: var(--space-4);
  }
  .learning-items li {
    align-items: flex-start;
    flex-direction: column;
  }
}
</style>
