import { test, expect } from '../fixtures'
import { capture } from '../helpers/screenshot'
import { env } from '../helpers/env'
import { login, openContacts, createContact } from '../helpers/bulwark'
import { expectInCollection } from '../helpers/dav'

test('a contact added in the web interface reaches CardDAV', async ({ page }) => {
  const user = env('PLAYWRIGHT_DEVICE_USER')
  const password = env('PLAYWRIGHT_DEVICE_PASSWORD')
  const lastName = `Contact${Date.now()}`

  await page.goto('/')
  await login(page, user, password)
  await openContacts(page)
  await createContact(page, 'Dave', lastName, `dave.${lastName.toLowerCase()}@example.com`)
  await capture(page, 'contact-created')

  await page.getByText(`Dave ${lastName}`).first().click()
  await expect(page.getByText(`dave.${lastName.toLowerCase()}@example.com`).first()).toBeVisible()
  await capture(page, 'contact-details')

  await expectInCollection(page.request, `/dav/card/${user}@${env('PLAYWRIGHT_FULL_DOMAIN')}/default/`, user, password, lastName)
})
