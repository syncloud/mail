import { test } from '../fixtures'
import { capture } from '../helpers/screenshot'
import { login, addContact } from '../helpers/roundcube'

test('a contact made in the old webmail', async ({ page }) => {
  await page.goto('/')
  await login(page, 'alice', 'Alice-Password1')
  await addContact(page, 'Carol', 'Contact', 'carol@example.com')
  await capture(page, 'contact-before-upgrade')
})
