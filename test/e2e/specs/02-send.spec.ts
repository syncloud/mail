import { test } from '@playwright/test'
import { shoot } from '../helpers/screenshot'
import { login, expectInbox, compose, expectInboxContains } from '../helpers/roundcube'

const user = process.env.PLAYWRIGHT_DEVICE_USER ?? 'user'
const password = process.env.PLAYWRIGHT_DEVICE_PASSWORD ?? 'Password1'
const domain = process.env.PLAYWRIGHT_FULL_DOMAIN ?? 'bookworm.com'

test.describe('mail send', () => {
  test('compose and send reaches inbox', async ({ page }, testInfo) => {
    await page.goto('/')
    await login(page, user, password)
    await expectInbox(page)

    const subject = `e2e-send-${Date.now()}`
    await compose(page, `${user}@${domain}`, subject, 'playwright web send test')
    await shoot(page, testInfo, 'sent')

    await expectInbox(page)
    await expectInboxContains(page, subject)
    await shoot(page, testInfo, 'received')
  })
})
