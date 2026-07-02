import { test } from '@playwright/test'
import { shoot } from '../helpers/screenshot'
import { login, expectInbox } from '../helpers/roundcube'

const user = process.env.PLAYWRIGHT_DEVICE_USER ?? 'user'
const password = process.env.PLAYWRIGHT_DEVICE_PASSWORD ?? 'Password1'

test.describe('mail pre-upgrade', () => {
  test('log in and reach inbox before upgrade', async ({ page }, testInfo) => {
    await page.goto('/')
    await shoot(page, testInfo, 'pre-upgrade-login')
    await login(page, user, password)
    await shoot(page, testInfo, 'pre-upgrade-login-submitted')
    await expectInbox(page)
    await shoot(page, testInfo, 'pre-upgrade-inbox')
  })
})
