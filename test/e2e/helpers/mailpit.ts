import { APIRequestContext, expect } from '@playwright/test'

const mailpitUrl = process.env.PLAYWRIGHT_MAILPIT_URL ?? 'http://mailpit:8025'

export async function expectRelayed(request: APIRequestContext, subject: string) {
  await expect.poll(async () => {
    const res = await request.get(`${mailpitUrl}/api/v1/search?query=${encodeURIComponent(subject)}`)
    if (!res.ok()) return 0
    const body = await res.json()
    return body.messages?.length ?? 0
  }, { timeout: 60000, intervals: [1000, 2000, 3000, 5000] }).toBeGreaterThan(0)
}
