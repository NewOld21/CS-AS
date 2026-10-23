import { test, expect } from '@playwright/test'
import AxeBuilder from '@axe-core/playwright'

test('desktop, tablet and mobile layouts render without horizontal overflow', async ({ page }) => {
  for (const width of [1440, 768, 390, 320]) {
    await page.setViewportSize({ width, height: 960 })
    for (const path of ['/', '/login', '/signup']) {
      await page.goto(path)
      await expect(page.locator('h1')).toBeVisible()
      expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(
        true,
      )
    }
  }
})
test('concept map works through keyboard and reduced motion stops decoration', async ({ page }) => {
  await page.goto('/')
  const node = page.getByRole('button', { name: '데이터베이스 개념 살펴보기' })
  await node.focus()
  await page.keyboard.press('Enter')
  await expect(node).toHaveAttribute('aria-pressed', 'true')
  await expect(page.locator('.concept-detail')).toContainText('인덱스와 트랜잭션')
  await page.getByRole('button', { name: '움직임 멈춤' }).click()
  await expect(page.getByRole('button', { name: '움직임 재생' })).toHaveAttribute(
    'aria-pressed',
    'true',
  )
  await page.emulateMedia({ reducedMotion: 'reduce' })
  expect(
    await page
      .locator('.node-object')
      .first()
      .evaluate((e) => getComputedStyle(e).animationName),
  ).toBe('none')
})
test('planned features are clearly marked and dialog returns keyboard focus', async ({ page }) => {
  await page.goto('/')
  const trigger = page.getByRole('button', { name: '퀴즈 풀기' })
  await trigger.click()
  await expect(page.getByRole('dialog')).toBeVisible()
  await expect(page.getByRole('dialog')).toContainText('준비하고')
  await page.keyboard.press('Escape')
  await expect(page.getByRole('dialog')).not.toBeVisible()
  await expect(trigger).toBeFocused()
})
test('mobile menu supports Escape and form validation keeps input visible', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 })
  await page.goto('/')
  const menu = page.getByRole('button', { name: '메뉴' })
  await menu.click()
  await page.getByRole('link', { name: '로그인', exact: true }).focus()
  await page.keyboard.press('Escape')
  await expect(menu).toBeFocused()
  await page.goto('/signup')
  await page.getByRole('button', { name: '내 계정 만들기' }).click()
  await expect(page.getByText('올바른 이메일 주소')).toBeVisible()
  await expect(page.locator('#email')).toBeFocused()
})
test('public landing and forms meet automated WCAG AA checks', async ({ page }) => {
  for (const path of ['/', '/login', '/signup']) {
    await page.goto(path)
    const result = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'])
      .analyze()
    expect(result.violations).toEqual([])
  }
})
test('auth errors and loading are real request states; no duplicate submission', async ({
  page,
}) => {
  let calls = 0
  await page.route('**/api/v1/auth/csrf', (route) =>
    route.fulfill({ json: { token: 'fixture-token' } }),
  )
  await page.route('**/api/v1/auth/login', async (route) => {
    calls++
    await new Promise((resolve) => setTimeout(resolve, 400))
    await route.fulfill({ status: 401, json: { code: 'INVALID_CREDENTIALS' } })
  })
  await page.goto('/login')
  await page.getByLabel('이메일', { exact: true }).fill('learner@example.com')
  await page.getByLabel('비밀번호', { exact: true }).fill('correct-horse-battery')
  await page.getByRole('button', { name: '로그인하기' }).click()
  await expect(page.getByRole('button', { name: '잠시만 기다려 주세요' })).toBeDisabled()
  await expect(page.getByRole('alert')).toContainText('이메일 또는 비밀번호')
  expect(calls).toBe(1)
})
test('account distinguishes offline loading from login expiry and renders no fake statistics', async ({
  page,
}) => {
  await page.route('**/api/v1/auth/me', (route) => route.abort('failed'))
  await page.goto('/account')
  await expect(page.getByRole('alert')).toContainText('서버에 연결할 수 없어요')
  await expect(page.getByRole('button', { name: '다시 불러오기' })).toBeVisible()
  await page.unroute('**/api/v1/auth/me')
  await page.route('**/api/v1/auth/me', (route) =>
    route.fulfill({ status: 401, json: { code: 'AUTH_REQUIRED' } }),
  )
  await page.getByRole('button', { name: '다시 불러오기' }).click()
  await expect(page).toHaveURL(/\/login$/)
})

test('quiz submission opens an owned contextual AS chat and renders trusted sources', async ({
  page,
}) => {
  let sessionCreated = false
  let answerStored = false
  const quiz = {
    id: 'quiz-1',
    version: 1,
    stem: '데이터베이스 인덱스의 단점은?',
    category: 'DATABASE',
    difficulty: 'EASY',
    origin: 'CURATED',
    concept_ids: ['concept:database-index'],
    options: [
      { id: 'option-1', position: 0, text: '쓰기 유지 비용이 든다' },
      { id: 'option-2', position: 1, text: '항상 저장 공간을 줄인다' },
    ],
  }
  await page.route('**/api/v1/auth/me', (route) =>
    route.fulfill({ json: { id: 'user-1', email: 'learner@example.com', nickname: '탐험가' } }),
  )
  await page.route('**/api/v1/auth/csrf', (route) => route.fulfill({ json: { token: 'csrf' } }))
  await page.route('**/api/v1/quiz/categories', (route) =>
    route.fulfill({ json: [{ id: 'DATABASE', name: '데이터베이스', quiz_count: 1 }] }),
  )
  await page.route('**/api/v1/quizzes?*', (route) =>
    route.fulfill({ json: { items: [quiz], next_cursor: null } }),
  )
  await page.route('**/api/v1/quizzes/quiz-1/attempts', async (route) => {
    expect(route.request().postDataJSON()).toEqual({ selected_option_id: 'option-2' })
    expect(route.request().headers()['idempotency-key']).toBeTruthy()
    await route.fulfill({
      json: {
        id: 'attempt-1',
        quiz,
        selected_option_id: 'option-2',
        correct_option_id: 'option-1',
        is_correct: false,
        explanation: '인덱스는 쓰기 시 함께 갱신해야 합니다.',
        sources: [],
        submitted_at: '2026-10-22T00:00:00Z',
      },
    })
  })
  const session = {
    id: 'chat-1',
    title: '데이터베이스 인덱스의 단점은?',
    quiz_id: 'quiz-1',
    attempt_id: 'attempt-1',
    created_at: '2026-10-22T00:00:00Z',
    updated_at: '2026-10-22T00:00:00Z',
  }
  await page.route('**/api/v1/chat/sessions?*', (route) =>
    route.fulfill({ json: { items: sessionCreated ? [session] : [], next_page: null } }),
  )
  await page.route('**/api/v1/chat/sessions', async (route) => {
    expect(route.request().postDataJSON()).toEqual({
      title: null,
      quiz_id: 'quiz-1',
      attempt_id: 'attempt-1',
    })
    sessionCreated = true
    await route.fulfill({ json: session })
  })
  await page.route('**/api/v1/chat/sessions/chat-1/messages*', async (route) => {
    if (route.request().method() === 'GET') {
      await route.fulfill({
        json: {
          items: answerStored
            ? [
                {
                  id: 'user-message-1',
                  role: 'USER',
                  content: '왜 틀렸어?',
                  status: null,
                  created_at: '2026-10-22T00:00:00Z',
                  request_id: null,
                  concept_ids: [],
                  sources: [],
                },
                {
                  id: 'message-1',
                  role: 'ASSISTANT',
                  content: '인덱스는 읽기를 빠르게 하지만 쓰기 때 유지 비용이 듭니다.',
                  status: 'answered',
                  created_at: '2026-10-22T00:00:01Z',
                  request_id: 'req-1',
                  concept_ids: ['concept:database-index'],
                  sources: [
                    {
                      source_id: 'postgres',
                      document_id: 'doc-1',
                      revision: '18',
                      chunk_id: 'chunk-1',
                      index_version: 'cs-v1',
                      title: 'PostgreSQL Indexes',
                      url: 'https://www.postgresql.org/docs/current/indexes.html',
                      locator: '11.1',
                      evidence_text: 'Saved evidence: indexes incur write maintenance costs.',
                      category: 'DATABASE',
                      technology_version: '18',
                    },
                  ],
                },
              ]
            : [],
          next_page: null,
        },
      })
      return
    }
    expect(route.request().headers()['idempotency-key']).toBeTruthy()
    answerStored = true
    await route.fulfill({
      json: {
        request_id: 'req-1',
        message_id: 'message-1',
        status: 'answered',
        answer: '인덱스는 읽기를 빠르게 하지만 쓰기 때 유지 비용이 듭니다.',
        sources: [
          {
            source_id: 'postgres',
            document_id: 'doc-1',
            revision: '18',
            chunk_id: 'chunk-1',
            index_version: 'cs-v1',
            title: 'PostgreSQL Indexes',
            url: 'https://www.postgresql.org/docs/current/indexes.html',
            locator: '11.1',
            evidence_text: 'Saved evidence: indexes incur write maintenance costs.',
            category: 'DATABASE',
            technology_version: '18',
          },
        ],
        concept_ids: ['concept:database-index'],
      },
    })
  })
  await page.goto('/learn')
  await page.getByText('항상 저장 공간을 줄인다').click()
  await page.getByRole('button', { name: '답안 제출' }).click()
  await expect(page.getByText('다시 연결해 볼 지점이에요.')).toBeVisible()
  await page.getByRole('button', { name: 'AS에게 질문하기' }).click()
  await page.getByRole('button', { name: '질문 보내기' }).click()
  await expect(page.getByText('인덱스는 읽기를 빠르게 하지만')).toBeVisible()
  const generatedQuiz = {
    id: 'generated-1',
    version: 1,
    stem: 'AI generated index question',
    category: 'DATABASE',
    difficulty: 'EASY',
    origin: 'AI_GENERATED',
    concept_ids: ['concept:database-index'],
    options: [1, 2, 3, 4].map((position) => ({
      id: `generated-option-${position}`,
      position,
      text: `Generated option ${position}`,
    })),
  }
  let generationCalls = 0
  const generatedAttempts: Array<{
    id: string
    quiz: typeof generatedQuiz
    selected_option_id: string
    correct_option_id: string
    is_correct: boolean
    explanation: string
    sources: []
    submitted_at: string
  }> = []
  await page.route('**/api/v1/quiz-generations', async (route) => {
    generationCalls++
    expect(route.request().headers()['idempotency-key']).toBeTruthy()
    await route.fulfill({
      json: { generation_id: 'generation-1', status: 'ready', quiz: generatedQuiz },
    })
  })
  await page.route('**/api/v1/quiz-generations/*', (route) =>
    route.fulfill({
      json: { generation_id: 'generation-1', status: 'ready', quiz: generatedQuiz },
    }),
  )
  await page.route('**/api/v1/quizzes/generated-1/attempts', (route) => {
    const body = route.request().postDataJSON()
    if (generatedAttempts.length) expect(body.retry_of_attempt_id).toBe(generatedAttempts[0]!.id)
    generatedAttempts.push({
      id: `generated-attempt-${generatedAttempts.length + 1}`,
      quiz: generatedQuiz,
      selected_option_id: body.selected_option_id,
      correct_option_id: 'generated-option-1',
      is_correct: body.selected_option_id === 'generated-option-1',
      explanation: 'Generated explanation after submission',
      sources: [],
      submitted_at: new Date().toISOString(),
    })
    return route.fulfill({
      json: {
        ...generatedAttempts.at(-1),
        quiz: generatedQuiz,
        selected_option_id: body.selected_option_id,
        correct_option_id: 'generated-option-1',
        is_correct: body.selected_option_id === 'generated-option-1',
        explanation: 'Generated explanation after submission',
        sources: [
          {
            source_id: 'fixture',
            document_id: 'doc-1',
            revision: 'r1',
            chunk_id: 'chunk-1',
            index_version: 'cs-v1',
            title: 'Generated evidence',
            url: 'https://example.org/index',
            locator: 'section:1',
            evidence_text: 'Actual saved generation evidence',
          },
        ],
      },
    })
  })
  await page.getByRole('button', { name: '관련 퀴즈 만들기' }).click()
  await expect(page.getByRole('heading', { name: 'AI generated index question' })).toBeVisible()
  await expect(page.getByText('AI 생성 문제 · 개인 학습')).toBeVisible()
  await expect(page.getByText('Generated explanation after submission')).not.toBeVisible()
  await page.getByText('Generated option 2').click()
  await page.getByRole('button', { name: '답안 제출' }).click()
  await expect(page.getByText('Generated explanation after submission')).toBeVisible()
  await page.getByRole('button', { name: 'Generated evidence · 생성 근거 보기' }).click()
  await expect(page.getByText('Actual saved generation evidence')).toBeVisible()
  await page.keyboard.press('Escape')
  await page.reload()
  await page.getByRole('button', { name: '이전 대화' }).click()
  await expect(page.getByRole('heading', { name: 'AI generated index question' })).toBeVisible()
  expect(generationCalls).toBe(1)
  await page.getByRole('button', { name: /PostgreSQL Indexes · 근거 보기/ }).click()
  await expect(page.getByRole('dialog')).toBeVisible()
  await expect(
    page.getByText('Saved evidence: indexes incur write maintenance costs.'),
  ).toBeVisible()
  await expect(page.getByRole('link', { name: /원본 문서 열기/ })).toHaveAttribute(
    'href',
    'https://www.postgresql.org/docs/current/indexes.html',
  )
  await page.keyboard.press('Escape')
  await expect(page.getByRole('dialog')).not.toBeVisible()
  await expect(page.getByRole('button', { name: /PostgreSQL Indexes · 근거 보기/ })).toBeFocused()
  await page.setViewportSize({ width: 390, height: 844 })
  await page.getByRole('button', { name: /PostgreSQL Indexes · 근거 보기/ }).click()
  await expect(page.getByRole('dialog')).toBeVisible()
  await page.getByRole('button', { name: '근거 패널 닫기' }).click()
  await page.reload()
  await page.getByRole('button', { name: '이전 대화' }).click()
  await expect(page.getByText('인덱스는 읽기를 빠르게 하지만')).toBeVisible()
  await page.route('**/api/v1/me/stats', (route) =>
    route.fulfill({
      json: {
        total_attempts: generatedAttempts.length + 1,
        correct_attempts: generatedAttempts.filter((a) => a.is_correct).length,
        accuracy:
          generatedAttempts.filter((a) => a.is_correct).length / (generatedAttempts.length + 1),
        unique_quizzes: 2,
        needs_review: generatedAttempts.at(-1)!.is_correct ? 1 : 2,
        resolved_reviews: generatedAttempts.at(-1)!.is_correct ? 1 : 0,
        by_category: [],
      },
    }),
  )
  await page.route('**/api/v1/me/wrong-answers?*', (route) => {
    const latest = generatedAttempts.at(-1)!
    const status = latest.is_correct ? 'RESOLVED' : 'NEEDS_REVIEW'
    const filter = new URL(route.request().url()).searchParams.get('status')
    const items =
      filter && filter !== status
        ? []
        : [
            {
              quiz: generatedQuiz,
              status,
              latest_attempt_id: latest.id,
              first_wrong_at: generatedAttempts[0]!.submitted_at,
              last_wrong_at: generatedAttempts[0]!.submitted_at,
              last_reviewed_at: latest.submitted_at,
              wrong_attempts: 1,
              retryable: true,
            },
          ]
    return route.fulfill({ json: { items, next_cursor: null, total_count: items.length } })
  })
  await page.route('**/api/v1/quizzes/generated-1', (route) =>
    route.fulfill({ json: generatedQuiz }),
  )
  await page.route('**/api/v1/me/attempts?*', (route) =>
    route.fulfill({
      json: {
        items: [...generatedAttempts].reverse(),
        next_cursor: null,
        total_count: generatedAttempts.length,
      },
    }),
  )
  await page.route('**/api/v1/me/attempts/generated-attempt-*', (route) =>
    route.fulfill({ json: generatedAttempts.find((a) => route.request().url().endsWith(a.id)) }),
  )
  await page.goto('/me/wrong-answers?origin=AI_GENERATED')
  await expect(page.locator('.learning-items')).toContainText('복습 필요')
  await page.getByRole('link', { name: '다시 풀기', exact: true }).click()
  await expect(page.getByText('Generated explanation after submission')).not.toBeVisible()
  await page.getByText('Generated option 1').click()
  await page.getByRole('button', { name: '답안 제출' }).click()
  await expect(page.getByText('정답이에요.', { exact: true })).toBeVisible()
  await page.getByRole('link', { name: '오답노트 확인' }).click()
  await page.getByLabel('복습 상태').selectOption('RESOLVED')
  await expect(page.locator('.learning-items')).toContainText('해결')
  await page.goto('/me?origin=AI_GENERATED')
  await expect(page.locator('.learning-items li')).toHaveCount(2)
  await expect(page.getByRole('region', { name: '학습 통계' })).toContainText('33.3%')
  await page.goto('/me/attempts/generated-attempt-1')
  await expect(page.getByText('당시 오답', { exact: true })).toBeVisible()
  expect(generatedAttempts).toHaveLength(2)
})
