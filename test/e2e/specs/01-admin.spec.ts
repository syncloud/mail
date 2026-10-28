import { test, expect } from '../fixtures'
import { capture } from '../helpers/screenshot'
import { env } from '../helpers/env'
import { login, openWebmailAdmin, openMailSettings } from '../helpers/bulwark'

test('a syncloud admin manages the webmail and the mail server', async ({ page }) => {
  const user = env('PLAYWRIGHT_DEVICE_USER')
  const password = env('PLAYWRIGHT_DEVICE_PASSWORD')

  await page.goto('/')
  await login(page, user, password)
  await expect(page.getByRole('button', { name: 'Mail settings', exact: true })).toBeVisible()
  await capture(page, 'admin-sidebar')

  const server = await openMailSettings(page, user, password)
  await expect(server.getByRole('heading', { name: 'Accounts' })).toBeVisible()
  await expect(server.getByText(`${user}@${env('PLAYWRIGHT_FULL_DOMAIN')}`).first()).toBeVisible()
  await capture(server, 'admin-mail-server')
  await server.close()

  await openWebmailAdmin(page)
  await capture(page, 'admin-webmail')
})
