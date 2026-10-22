import { defineConfig } from '@playwright/test'
export default defineConfig({
  testDir: './tests/e2e',
  outputDir: '../reports/ui-qa/test-results',
  timeout: 30000,
  fullyParallel: false,
  reporter: [
    ['list'],
    ['html', { outputFolder: '../reports/ui-qa/playwright-report', open: 'never' }],
  ],
  use: {
    baseURL: 'http://localhost:5173',
    channel: process.env.PLAYWRIGHT_CHANNEL,
    screenshot: 'only-on-failure',
    trace: 'retain-on-failure',
  },
  webServer: { command: 'npm run dev', url: 'http://localhost:5173', reuseExistingServer: true },
})
