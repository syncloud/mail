import { test, expect } from '@playwright/test'
import { shoot } from '../helpers/screenshot'
import { login, expectInbox } from '../helpers/roundcube'

const user = process.env.PLAYWRIGHT_DEVICE_USER ?? 'user'
const password = process.env.PLAYWRIGHT_DEVICE_PASSWORD ?? 'Password1'

test.describe('mail admin relay', () => {
  test('configure outbound relay', async ({ page }, testInfo) => {
    await page.goto('/')
    await login(page, user, password)
    await expectInbox(page)
    await shoot(page, testInfo, 'inbox')

    await page.getByTestId('nav-admin').click()
    await expect(page.getByTestId('admin-title')).toBeVisible()
    await shoot(page, testInfo, 'admin')

    await page.getByTestId('relay-enabled').click()
    await page.getByTestId('relay-host').fill('smtp.gmail.com')
    await page.getByTestId('relay-port').fill('587')
    await page.getByTestId('relay-user').fill('user@gmail.com')
    await page.getByTestId('relay-password').fill('app-password')
    await shoot(page, testInfo, 'relay-filled')

    await page.getByTestId('relay-save').click()
    await expect(page.getByText('Saved')).toBeVisible()
    await shoot(page, testInfo, 'relay-saved')
  })
})
