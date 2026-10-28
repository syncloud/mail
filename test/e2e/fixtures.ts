import { test as base, expect } from '@playwright/test'
import * as path from 'node:path'
import { capture } from './helpers/screenshot'

export const test = base.extend<{ failureScreenshot: void }>({
  failureScreenshot: [
    async ({ page }, use, info) => {
      await use()
      if (info.status !== info.expectedStatus) {
        await capture(page, `failed-${path.basename(info.file, '.spec.ts')}-line-${info.line}`)
      }
    },
    { auto: true },
  ],
})

export { expect }
