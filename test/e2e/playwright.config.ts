import { defineConfig, devices } from '@playwright/test'
import { env } from './helpers/env'

export default defineConfig({
  testDir: './specs',
  fullyParallel: false,
  workers: 1,
  retries: 0,
  maxFailures: 1,
  reporter: [['list']],
  globalTeardown: './globalTeardown.ts',
  timeout: 180_000,
  expect: { timeout: 30_000 },
  use: {
    baseURL: `https://${env('PLAYWRIGHT_APP_DOMAIN')}`,
    ignoreHTTPSErrors: true,
  },
  projects: [
    {
      name: 'desktop',
      use: { ...devices['Desktop Chrome'], viewport: { width: 1440, height: 960 } },
    },
    {
      name: 'mobile',
      use: { ...devices['Pixel 5'] },
    },
  ],
})
