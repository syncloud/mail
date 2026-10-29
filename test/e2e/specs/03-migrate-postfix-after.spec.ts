import { test, expect } from '../fixtures'
import { capture } from '../helpers/screenshot'
import { login, expectMessage, openFolder, openContacts } from '../helpers/bulwark'

test('mail, folders and contacts from the old webmail are visible', async ({ page }) => {
  await page.goto('/')
  await login(page, 'alice', 'Alice-Password1')

  await test.step('a user outside the syncloud group gets no admin', async () => {
    await expect(page.getByRole('link', { name: 'Admin', exact: true })).toHaveCount(0)
  })

  await test.step('inbox keeps its message and its star', async () => {
    await expectMessage(page, 'migrated-alice-inbox')
    await expect(page.getByTestId('email-list-item').filter({ hasText: 'migrated-alice-inbox' }))
      .toContainText('Starred')
    await expect(page.getByTestId('email-list-item').filter({ hasText: 'migrated-alice-project' })).toHaveCount(0)
    await capture(page, 'inbox-after-upgrade')
  })

  await test.step('the folder the user made is there with its message', async () => {
    await openFolder(page, 'Projects')
    await expectMessage(page, 'migrated-alice-project')
    await capture(page, 'folder-after-upgrade')
  })

  await test.step('the contact made in roundcube is in the address book', async () => {
    await openContacts(page)
    await expect(page.getByText('Carol Contact')).toBeVisible()
    await expect(page.getByText('carol@example.com')).toBeVisible()
    await capture(page, 'contacts-after-upgrade')
  })
})
