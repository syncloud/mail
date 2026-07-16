import { test, expect } from '@playwright/test'
import { shoot } from '../helpers/screenshot'
import { login, expectInbox, compose } from '../helpers/roundcube'
import { expectRelayed } from '../helpers/mailpit'

const user = process.env.PLAYWRIGHT_DEVICE_USER ?? 'user'
const password = process.env.PLAYWRIGHT_DEVICE_PASSWORD ?? 'Password1'
const relayHost = process.env.PLAYWRIGHT_RELAY_HOST ?? 'mailpit'
const relayPort = process.env.PLAYWRIGHT_RELAY_PORT ?? '1025'
const relayUser = process.env.PLAYWRIGHT_RELAY_USER ?? 'relayuser'
const relayPassword = process.env.PLAYWRIGHT_RELAY_PASSWORD ?? 'relaypass'

test.describe('mail admin relay', () => {
  test('configure relay and send through it', async ({ page, request }, testInfo) => {
    await page.goto('/')
    await login(page, user, password)
    await expectInbox(page)

    await page.getByTestId('nav-admin').click()
    await expect(page.getByTestId('admin-title')).toBeVisible()
    await shoot(page, testInfo, 'admin')

    await page.getByTestId('relay-enabled').click()
    await page.getByTestId('relay-host').fill(relayHost)
    await page.getByTestId('relay-port').fill(relayPort)
    await page.getByTestId('relay-user').fill(relayUser)
    await page.getByTestId('relay-password').fill(relayPassword)
    await page.getByTestId('relay-save').click()
    await expect(page.getByText('Saved')).toBeVisible()
    await shoot(page, testInfo, 'relay-saved')

    await page.getByTestId('nav-mail').click()
    await expectInbox(page)

    const subject = `e2e-relay-${Date.now()}`
    await compose(page, 'relayed@example.com', subject, 'playwright relay send test')
    await shoot(page, testInfo, 'relay-sent')

    await expectRelayed(request, subject)
  })
})
