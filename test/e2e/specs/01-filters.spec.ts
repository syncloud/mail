import { test, expect } from '../fixtures'
import { capture } from '../helpers/screenshot'
import { env } from '../helpers/env'
import { login, createFolder, createRule, backToMail, compose, openFolder, expectMessage } from '../helpers/bulwark'

test('a filter rule files matching mail into a folder on the server', async ({ page }) => {
  const user = env('PLAYWRIGHT_DEVICE_USER')
  const token = `invoice-${Date.now()}`
  const folder = `Receipts${Date.now()}`

  await page.goto('/')
  await login(page, user, env('PLAYWRIGHT_DEVICE_PASSWORD'))
  await createFolder(page, folder)
  await capture(page, 'filter-folder')
  await createRule(page, `File ${token}`, token, folder)
  await capture(page, 'filter-rule')

  await backToMail(page)
  await compose(page, `${user}@${env('PLAYWRIGHT_FULL_DOMAIN')}`, `${token} for October`, 'should be filed by the rule')

  await openFolder(page, folder)
  await expectMessage(page, `${token} for October`)
  await capture(page, 'filter-filed')

  await openFolder(page, 'Inbox')
  await expect(page.getByTestId('email-list-item').filter({ hasText: token })).toHaveCount(0)
})
