import { test, expect } from '@playwright/test'
test('real PostgreSQL signup, duplicate, login, reload and logout through unchanged API', async ({
  page,
}) => {
  // Opt in to a dedicated test backend; never register test accounts in the development DB.
  const target = process.env.CSAS_E2E_API
  test.skip(!target, 'Set CSAS_E2E_API to the isolated PostgreSQL test backend')
  await page.route('**/api/v1/**', async (route) => {
    const url = new URL(route.request().url())
    const response = await route.fetch({ url: target + url.pathname })
    await route.fulfill({ response })
  })
  const email = `ui-${Date.now()}@example.com`
  const password = 'correct-horse-battery'
  await page.goto('/signup')
  await page.getByLabel('이메일', { exact: true }).fill(email)
  await page.getByLabel('비밀번호', { exact: true }).fill(password)
  await page.getByLabel('닉네임').fill('UI 탐험가')
  await page.getByRole('button', { name: '내 계정 만들기' }).click()
  await expect(page.getByText('첫 연결이 만들어졌어요.')).toBeVisible()
  await page.goto('/signup')
  await page.getByLabel('이메일', { exact: true }).fill(email.toUpperCase())
  await page.getByLabel('비밀번호', { exact: true }).fill(password)
  await page.getByRole('button', { name: '내 계정 만들기' }).click()
  await expect(page.getByRole('alert')).toContainText('이미 가입한 이메일')
  await page.goto('/login')
  await page.getByLabel('이메일', { exact: true }).fill(email)
  await page.getByLabel('비밀번호', { exact: true }).fill('incorrect-password')
  await page.getByRole('button', { name: '로그인하기' }).click()
  await expect(page.getByRole('alert')).toContainText('이메일 또는 비밀번호')
  await page.getByLabel('비밀번호', { exact: true }).fill(password)
  await page.getByRole('button', { name: '로그인하기' }).click()
  await expect(page).toHaveURL(/\/account$/)
  await expect(page.getByText(email, { exact: true })).toBeVisible()
  await page.reload()
  await expect(page.getByText(email, { exact: true })).toBeVisible()
  await page.setViewportSize({ width: 1440, height: 1000 })
  await page.screenshot({ path: '../reports/ui-qa/account-desktop.png', fullPage: true })
  await page.setViewportSize({ width: 390, height: 844 })
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true)
  await page.screenshot({ path: '../reports/ui-qa/account-mobile.png', fullPage: true })
  await page.getByRole('button', { name: '로그아웃' }).click()
  await expect(page).toHaveURL(/\/login$/)
  await page.goto('/account')
  await expect(page).toHaveURL(/\/login$/)
})
