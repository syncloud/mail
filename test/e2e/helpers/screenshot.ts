import { Page } from '@playwright/test'
import * as path from 'node:path'
import * as fs from 'node:fs'
import { env } from './env'

export async function capture(page: Page, name: string) {
  const dir = env('PLAYWRIGHT_ARTIFACT_DIR')
  fs.mkdirSync(dir, { recursive: true })
  await page.screenshot({ path: path.join(dir, `${name}-${env('PLAYWRIGHT_PROJECT')}.png`) })
}
