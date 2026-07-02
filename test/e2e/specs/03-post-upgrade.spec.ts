import { test } from '@playwright/test'
import { shoot } from '../helpers/screenshot'
import { login, expectInbox } from '../helpers/roundcube'

const user = process.env.PLAYWRIGHT_DEVICE_USER ?? 'user'
const password = process.env.PLAYWRIGHT_DEVICE_PASSWORD ?? 'Password1'

test.describe('mail post-upgrade', () => {
  test('log in and reach inbox after upgrade', async ({ page }, testInfo) => {
    await page.goto('/')
    await shoot(page, testInfo, 'post-upgrade-login')
    await login(page, user, password)
    await shoot(page, testInfo, 'post-upgrade-login-submitted')
    await expectInbox(page)
    await shoot(page, testInfo, 'post-upgrade-inbox')
  })
})
