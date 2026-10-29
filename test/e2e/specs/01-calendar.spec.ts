import { test } from '../fixtures'
import { capture } from '../helpers/screenshot'
import { env } from '../helpers/env'
import { login, openCalendar, createEvent } from '../helpers/bulwark'
import { expectInCollection } from '../helpers/dav'

test('an event added in the web interface reaches CalDAV', async ({ page }) => {
  const user = env('PLAYWRIGHT_DEVICE_USER')
  const password = env('PLAYWRIGHT_DEVICE_PASSWORD')
  const title = `Team sync ${Date.now()}`

  await page.goto('/')
  await login(page, user, password)
  await openCalendar(page)
  await capture(page, 'calendar')
  await createEvent(page, title)
  await capture(page, 'event-created')

  await expectInCollection(page.request, `/dav/cal/${user}@${env('PLAYWRIGHT_FULL_DOMAIN')}/default/`, user, password, title)
})
