import { test, expect } from '@playwright/test'
import AxeBuilder from '@axe-core/playwright'
import fs from 'node:fs'

test('standalone chat restores, isolates sessions, shows citations and supports mobile', async ({
  page,
}) => {
  const sessions: Array<{ id: string; title: string; quiz_id: null; attempt_id: null }> = []
  const transcripts: Record<string, object[]> = {}
  const source = {
    source_id: 'postgresql',
    document_id: 'doc:1',
    revision: '17',
    chunk_id: 'chunk:1',
    index_version: 'test-v1',
    title: 'PostgreSQL isolation',
    url: 'https://www.postgresql.org/docs/17/transaction-iso.html',
    locator: '13.2',
    evidence_text: 'Read Committed uses a new snapshot for each command.',
  }
  await page.route('**/api/v1/**', async (route) => {
    const path = new URL(route.request().url()).pathname
    const method = route.request().method()
    if (path.endsWith('/auth/me'))
      return route.fulfill({
        json: { id: 'owner', email: 'owner@example.test', nickname: '학습자' },
      })
    if (path.endsWith('/auth/csrf')) return route.fulfill({ json: { token: 'csrf' } })
    if (path.endsWith('/chat/status'))
      return route.fulfill({
        json: {
          mode: 'gms',
          model: 'gpt-5-mini',
          live: true,
          configured: true,
          corpus_kind: 'active',
        },
      })
    if (path.endsWith('/chat/sessions')) {
      if (method === 'POST') {
        const session = {
          id: `session-${sessions.length + 1}`,
          title: 'CS 자유 학습',
          quiz_id: null,
          attempt_id: null,
        }
        sessions.unshift(session)
        transcripts[session.id] = []
        return route.fulfill({ json: session })
      }
      return route.fulfill({ json: { items: sessions, next_page: null } })
    }
    const match = path.match(/sessions\/([^/]+)\/messages/)
    if (match) {
      const id = match[1]!
      if (method === 'POST') {
        const question = route.request().postDataJSON().question
        const transcript = transcripts[id]!
        transcript.push(
          {
            id: `u-${transcript.length}`,
            role: 'USER',
            content: question,
            sources: [],
            status: null,
          },
          {
            id: `a-${transcript.length}`,
            role: 'ASSISTANT',
            content: '**격리 수준**은 동시 실행을 제어합니다. [1]\n```sql\nSELECT 1;\n```',
            status: 'answered',
            sources: [source],
          },
        )
        return route.fulfill({ json: { status: 'answered' } })
      }
      return route.fulfill({ json: { items: transcripts[id], next_page: null } })
    }
    return route.fulfill({ status: 404, json: { code: 'NOT_FOUND' } })
  })
  await page.goto('/chat')
  await page.getByLabel('CS 질문', { exact: true }).fill('트랜잭션이 뭐야?')
  await page.getByLabel('CS 질문', { exact: true }).press('Enter')
  await expect(page.getByText('트랜잭션이 뭐야?', { exact: true })).toBeVisible()
  await expect(page.getByRole('button', { name: '근거 [1] 보기', exact: true })).toBeVisible()
  await page.getByRole('button', { name: '근거 [1] 보기', exact: true }).click()
  await expect(page.getByRole('dialog')).toContainText(source.evidence_text)
  await expect(page.getByRole('link', { name: /원본 문서 열기/ })).toHaveAttribute(
    'href',
    source.url,
  )
  await page.keyboard.press('Escape')
  await page.getByLabel('CS 질문', { exact: true }).fill('더 쉽게')
  await page.getByLabel('CS 질문', { exact: true }).press('Shift+Enter')
  await expect(page.getByLabel('CS 질문', { exact: true })).toHaveValue('더 쉽게\n')
  await page.getByRole('button', { name: '질문 보내기', exact: true }).click()
  await expect(page.locator('.from-user')).toHaveCount(2)
  await page.reload()
  await expect(page.locator('.from-user')).toHaveCount(2)
  await page.getByRole('button', { name: '새 대화', exact: true }).click()
  await expect(page.locator('.from-user')).toHaveCount(0)
  await page.getByLabel('CS 질문', { exact: true }).fill('네트워크가 뭐야?')
  await page.getByRole('button', { name: '질문 보내기', exact: true }).click()
  await expect(page.locator('.from-user')).toHaveCount(1)
  await expect(page.locator('.conversation-log')).not.toContainText('트랜잭션이 뭐야?')
  fs.mkdirSync('../reports/checklist/evidence', { recursive: true })
  await page.screenshot({
    path: '../reports/checklist/evidence/standalone-desktop.png',
    fullPage: true,
  })
  await page.setViewportSize({ width: 390, height: 844 })
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true)
  await page.screenshot({
    path: '../reports/checklist/evidence/standalone-mobile.png',
    fullPage: true,
  })
  const axe = await new AxeBuilder({ page })
    .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'])
    .analyze()
  expect(axe.violations).toEqual([])
})

test('unconfigured AI and insufficient evidence are explicitly shown', async ({ page }) => {
  await page.route('**/api/v1/auth/me', (route) =>
    route.fulfill({ json: { id: 'u', email: 'u@example.test' } }),
  )
  await page.route('**/api/v1/chat/status', (route) =>
    route.fulfill({ json: { configured: false, live: false, error_code: 'GMS_KEY_MISSING' } }),
  )
  await page.route('**/api/v1/chat/sessions?*', (route) =>
    route.fulfill({ json: { items: [], next_page: null } }),
  )
  await page.route('**/api/v1/chat/sessions/s/messages?*', (route) =>
    route.fulfill({
      json: {
        items: [
          {
            id: 'a',
            role: 'ASSISTANT',
            content: null,
            status: 'insufficient_evidence',
            sources: [],
          },
        ],
        next_page: null,
      },
    }),
  )
  await page.goto('/chat?session=s')
  await expect(page.getByRole('alert')).toContainText('GMS 키가 설정되지 않았습니다.')
  await expect(page.getByText('확인된 근거 문서가 없습니다.')).toBeVisible()
  await expect(
    page.getByText('현재 확보된 CS 문서에서는 답할 충분한 근거를 확인하지 못했습니다.'),
  ).toBeVisible()
})
