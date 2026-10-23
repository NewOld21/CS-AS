import { test, expect } from '@playwright/test'
import AxeBuilder from '@axe-core/playwright'

const quiz = {
  id: 'quiz-1',
  version: 1,
  stem: '인덱스의 유지 비용은?',
  category: 'DATABASE',
  difficulty: 'EASY',
  origin: 'AI_GENERATED',
  concept_ids: ['concept:database-index'],
  options: [
    { id: 'o1', position: 1, text: '쓰기 때 갱신 비용' },
    { id: 'o2', position: 2, text: '비용 없음' },
  ],
}
const attempt = {
  id: 'attempt-1',
  quiz,
  selected_option_id: 'o2',
  correct_option_id: 'o1',
  is_correct: false,
  explanation: '쓰기 때 인덱스 갱신이 필요합니다.',
  sources: [],
  submitted_at: '2026-10-23T00:00:00Z',
}
const stats = {
  total_attempts: 1,
  correct_attempts: 0,
  accuracy: 0,
  unique_quizzes: 1,
  needs_review: 1,
  resolved_reviews: 0,
  by_category: [{ category: 'DATABASE', total_attempts: 1, correct_attempts: 0, accuracy: 0 }],
}

test.beforeEach(async ({ page }) => {
  await page.route('**/api/v1/auth/me', (route) =>
    route.fulfill({ json: { id: 'owner', email: 'owner@example.com', nickname: '학습자' } }),
  )
  await page.route('**/api/v1/me/stats', (route) => route.fulfill({ json: stats }))
})

test('history uses server pagination and filters, and fits mobile', async ({ page }) => {
  const seen: string[] = []
  await page.route('**/api/v1/me/attempts?*', (route) => {
    const url = new URL(route.request().url())
    seen.push(url.search)
    return route.fulfill({
      json: {
        items: [attempt],
        next_cursor: url.searchParams.has('cursor') ? null : 'opaque-cursor',
        total_count: 2,
      },
    })
  })
  await page.setViewportSize({ width: 390, height: 844 })
  await page.goto('/me')
  await expect(page.getByRole('region', { name: '학습 통계' })).toContainText('0%')
  await expect(page.getByRole('link', { name: quiz.stem })).toBeVisible()
  await page.getByRole('button', { name: '다음 페이지' }).click()
  await expect(page.getByRole('button', { name: '다음 페이지' })).toBeDisabled()
  expect(seen.at(-1)).toContain('cursor=opaque-cursor')
  await page.getByLabel('문제 유형').selectOption('AI_GENERATED')
  await expect.poll(() => seen.at(-1)).toContain('origin=AI_GENERATED')
  expect(seen.at(-1)).not.toContain('cursor=')
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true)
  const accessibility = await new AxeBuilder({ page })
    .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'])
    .analyze()
  expect(accessibility.violations).toEqual([])
})

test('notebook opens an ungraded retry and reuses the key after a lost response', async ({
  page,
}) => {
  await page.route('**/api/v1/me/wrong-answers?*', (route) =>
    route.fulfill({
      json: {
        items: [
          {
            quiz,
            status: 'NEEDS_REVIEW',
            latest_attempt_id: attempt.id,
            first_wrong_at: attempt.submitted_at,
            last_wrong_at: attempt.submitted_at,
            last_reviewed_at: null,
            wrong_attempts: 1,
            retryable: true,
          },
        ],
        total_count: 1,
        next_cursor: null,
      },
    }),
  )
  await page.route('**/api/v1/quiz/categories', (route) => route.fulfill({ json: [] }))
  await page.route('**/api/v1/quizzes/quiz-1', (route) => route.fulfill({ json: quiz }))
  await page.route('**/api/v1/auth/csrf', (route) => route.fulfill({ json: { token: 'csrf' } }))
  const keys: string[] = []
  await page.route('**/api/v1/quizzes/quiz-1/attempts', async (route) => {
    keys.push(route.request().headers()['idempotency-key']!)
    expect(route.request().postDataJSON()).toEqual({
      selected_option_id: 'o1',
      retry_of_attempt_id: 'attempt-1',
    })
    if (keys.length === 1) await route.abort('failed')
    else
      await route.fulfill({
        json: { ...attempt, id: 'retry-1', selected_option_id: 'o1', is_correct: true },
      })
  })
  await page.goto('/me/wrong-answers')
  await page.getByRole('link', { name: '다시 풀기', exact: true }).click()
  await expect(page.getByText(attempt.explanation)).not.toBeVisible()
  await page.getByRole('radio', { name: /쓰기 때 갱신 비용/ }).check()
  await page.getByRole('button', { name: '답안 제출' }).click()
  await expect(page.getByRole('alert')).toBeVisible()
  await expect(page.getByRole('radio').first()).toBeDisabled()
  await page.reload()
  await page.getByRole('button', { name: '제출 결과 다시 확인' }).click()
  await expect(page.getByText('정답이에요.', { exact: true })).toBeVisible()
  expect(keys).toHaveLength(2)
  expect(keys[0]).toBe(keys[1])
})

test('empty history, unavailable statistics, retired snapshots and expiry are distinct', async ({
  page,
}) => {
  await page.route('**/api/v1/me/attempts?*', (route) =>
    route.fulfill({ json: { items: [], total_count: 0, next_cursor: null } }),
  )
  await page.route('**/api/v1/me/stats', (route) =>
    route.fulfill({ status: 503, json: { code: 'UNAVAILABLE' } }),
  )
  await page.goto('/me')
  await expect(page.getByText('해당 조건의 풀이 기록이 없습니다.')).toBeVisible()
  await expect(page.getByRole('button', { name: '통계 다시 불러오기' })).toBeVisible()
  await page.route('**/api/v1/me/attempts/attempt-1', (route) => route.fulfill({ json: attempt }))
  await page.route('**/api/v1/quizzes/quiz-1', (route) =>
    route.fulfill({ status: 404, json: { code: 'QUIZ_NOT_FOUND' } }),
  )
  await page.goto('/me/attempts/attempt-1')
  await expect(page.getByText(attempt.explanation)).toBeVisible()
  await expect(page.getByRole('link', { name: '다시 풀기' })).not.toBeVisible()
  await page.route('**/api/v1/auth/me', (route) =>
    route.fulfill({ status: 401, json: { code: 'AUTH_REQUIRED' } }),
  )
  await page.goto('/me')
  await expect(page).toHaveURL(/\/login$/)
})
