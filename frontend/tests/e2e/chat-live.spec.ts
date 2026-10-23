import { test, expect } from '@playwright/test'
import fs from 'node:fs'

test('live GMS standalone multi-turn chat and owned quiz AS', async ({ page }) => {
  test.skip(
    !process.env.CSAS_CHAT_E2E_API,
    'Requires dedicated test PostgreSQL backend and configured GMS/Chroma',
  )
  test.setTimeout(300000)
  await page.route('**/api/v1/**', async (route) => {
    const original = new URL(route.request().url())
    const response = await route.fetch({
      url: `${process.env.CSAS_CHAT_E2E_API}${original.pathname}${original.search}`,
      timeout: 125000,
    })
    await route.fulfill({ response })
  })
  const email = `chat-${Date.now()}@example.test`
  await page.goto('/signup')
  await page.getByLabel('이메일', { exact: true }).fill(email)
  await page.getByLabel('비밀번호', { exact: true }).fill('correct-horse-battery')
  const nickname = page.getByLabel('닉네임', { exact: true })
  if (await nickname.count()) await nickname.fill('RAG 점검')
  await page.getByRole('button', { name: '내 계정 만들기' }).click()
  await page.waitForURL(/signup/, { timeout: 15000 })
  await expect(page.getByText('첫 연결이 만들어졌어요.')).toBeVisible({ timeout: 15000 })
  await page.goto('/login')
  await page.getByLabel('이메일', { exact: true }).fill(email)
  await page.getByLabel('비밀번호', { exact: true }).fill('correct-horse-battery')
  await page.getByRole('button', { name: '로그인하기' }).click()
  await expect(page).toHaveURL(/\/account$/, { timeout: 15000 })
  await page.goto('/chat')
  await page
    .getByLabel('CS 질문', { exact: true })
    .fill('PostgreSQL의 Read Committed는 각 SELECT에 어떤 스냅샷을 사용하나요?')
  await page.getByRole('button', { name: '질문 보내기', exact: true }).click()
  await expect(page.locator('.chat-sources button').first()).toBeVisible({ timeout: 120000 })
  await page
    .getByLabel('CS 질문', { exact: true })
    .fill('그럼 같은 트랜잭션에서도 조회 결과가 바뀔 수 있다는 뜻인가요? 쉽게 설명해줘.')
  await page.getByRole('button', { name: '질문 보내기', exact: true }).click()
  await expect(page.locator('.from-as')).toHaveCount(2, { timeout: 120000 })
  await expect(page.locator('.from-as').last().locator('.chat-sources button').first()).toBeVisible(
    { timeout: 120000 },
  )
  await page.reload()
  await expect(page.locator('.from-user')).toHaveCount(2)
  fs.mkdirSync('../reports/checklist/evidence', { recursive: true })
  await page.screenshot({
    path: '../reports/checklist/evidence/live-gms-multiturn.png',
    fullPage: true,
  })
  await page.locator('.chat-sources button').last().click()
  await expect(page.getByRole('dialog')).toBeVisible()
  await page.screenshot({
    path: '../reports/checklist/evidence/live-gms-evidence.png',
    fullPage: true,
  })
  await page.keyboard.press('Escape')
  await page.getByRole('button', { name: '새 대화', exact: true }).click()
  await expect(page.locator('.from-user')).toHaveCount(0)
  await page.goto('/learn?quiz_id=10000000-0000-0000-0000-000000000008')
  await page.getByRole('radio').nth(1).check()
  await page.getByRole('button', { name: '답안 제출', exact: true }).click()
  await page.getByRole('button', { name: 'AS에게 질문하기' }).click()
  await page.getByRole('button', { name: '질문 보내기', exact: true }).click()
  await expect(page.locator('.chat-panel .source-list button').first()).toBeVisible({
    timeout: 120000,
  })
  await page.screenshot({ path: '../reports/checklist/evidence/live-quiz-as.png', fullPage: true })
  await page.getByRole('button', { name: '관련 퀴즈 만들기', exact: true }).click()
  await expect(page.getByText('AI 생성 문제 · 개인 학습', { exact: true })).toBeVisible({
    timeout: 120000,
  })
  await page.getByRole('radio').first().check()
  await page.getByRole('button', { name: '답안 제출', exact: true }).click()
  await expect(page.locator('.attempt-feedback')).toBeVisible()
  await page.goto('/me?origin=AI_GENERATED')
  await expect(page.locator('.learning-items li')).toHaveCount(1)
  await page.screenshot({
    path: '../reports/checklist/evidence/live-generated-history.png',
    fullPage: true,
  })
})
