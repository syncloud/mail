import { test } from '../fixtures'
import { capture } from '../helpers/screenshot'
import { env } from '../helpers/env'
import { login, compose, expectMessage, openContacts } from '../helpers/bulwark'

test('log in, send to yourself and open contacts', async ({ page }) => {
  const user = env('PLAYWRIGHT_DEVICE_USER')
  const subject = `e2e-send-${env('PLAYWRIGHT_PROJECT')}-${Date.now()}`

  await page.goto('/')
  await capture(page, 'login')
  await login(page, user, env('PLAYWRIGHT_DEVICE_PASSWORD'))
  await capture(page, 'inbox')

  await compose(page, `${user}@${env('PLAYWRIGHT_FULL_DOMAIN')}`, subject, 'sent from the web interface')
  await expectMessage(page, subject)
  await capture(page, 'received')

  await openContacts(page)
  await capture(page, 'contacts')
})
