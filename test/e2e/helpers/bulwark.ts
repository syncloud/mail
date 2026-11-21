import { Page, expect } from '@playwright/test'

export async function login(page: Page, user: string, password: string) {
  const responses: string[] = []
  page.on('response', (response) => {
    if (/\/api\/(auth|oidc|firstfactor)|\/jmap\/session|\/auth\/callback/.test(response.url())) {
      responses.push(`${response.status()} ${response.url()}`)
    }
  })
  await page.getByRole('button', { name: 'Sign in with SSO' }).click()
  await page.locator('#username-textfield').fill(user)
  await page.locator('#password-textfield').fill(password)
  await page.locator('#sign-in-button').click()
  const accountSwitcher = page.getByTestId('account-switcher').first()
  const passkeySkip = page.getByTestId('passkey-skip')
  try {
    await expect(passkeySkip.or(accountSwitcher).first()).toBeVisible({ timeout: 60_000 })
    if (await passkeySkip.isVisible()) {
      await passkeySkip.click()
    }
    await expect(accountSwitcher).toBeVisible({ timeout: 60_000 })
  } catch (e) {
    console.log(`[login] url=${page.url()}`)
    console.log(`[login] responses=\n${responses.join('\n')}`)
    console.log(`[login] html=\n${(await page.content().catch(() => '')).slice(0, 4000)}`)
    throw e
  }
}

export async function expectMessage(page: Page, subject: string) {
  await expect(page.getByText(subject, { exact: true }).first()).toBeVisible({ timeout: 60_000 })
}

export async function openFolder(page: Page, name: string) {
  const menu = page.getByRole('button', { name: 'Toggle menu' })
  if (!(await menu.isVisible())) {
    await page.getByTestId('folder-row').filter({ hasText: name }).first().click()
    return
  }
  await menu.click()
  await page.getByText(name, { exact: true }).locator('visible=true').first().click()
}

export async function compose(page: Page, to: string, subject: string, body: string) {
  await page.getByRole('button', { name: 'Compose' }).first().click()
  const composer = page.getByTestId('email-composer')
  await expect(composer).toBeVisible()
  const recipients = composer.getByTestId('composer-to')
  const recipient = recipients.locator('input')
  await recipient.fill(to)
  await recipient.press('Enter')
  await expect(recipients).toContainText(to)
  await expect(recipient).toHaveValue('')
  await expect(recipient).toBeFocused()
  const subjectInput = composer.getByTestId('composer-subject')
  await subjectInput.fill(subject)
  await expect(subjectInput).toHaveValue(subject)
  await expect(recipient).toHaveValue('')
  await composer.locator('[contenteditable=true]').first().fill(body)
  await composer.getByRole('button', { name: 'Send', exact: true }).click()
  await expect(composer).toBeHidden()
}

export async function openContacts(page: Page) {
  await page.locator('a[href="/contacts"]').first().click()
  await expect(page.getByPlaceholder('Search contacts...', { exact: true })).toBeVisible()
}

export async function createContact(page: Page, firstName: string, lastName: string, email: string) {
  await page.getByRole('button', { name: 'New', exact: true }).locator('visible=true').first().click()
  await page.getByRole('menuitem', { name: 'New contact', exact: true }).click()
  await page.getByPlaceholder('First name').fill(firstName)
  await page.getByPlaceholder('Last name').fill(lastName)
  await page.getByPlaceholder('email@example.com').fill(email)
  await page.getByRole('button', { name: 'Save', exact: true }).click()
  await expect(page.getByText(`${firstName} ${lastName}`).locator('visible=true').first()).toBeVisible()
}

export async function openCalendar(page: Page) {
  await page.locator('a[href="/calendar"]').first().click()
  await expect(page.getByRole('button', { name: 'Create event' }).locator('visible=true').first()).toBeVisible()
}

export async function createEvent(page: Page, title: string) {
  await page.getByRole('button', { name: 'Create event' }).locator('visible=true').first().click()
  await page.getByPlaceholder('Title').fill(title)
  await page.getByRole('button', { name: 'Save', exact: true }).click()
  await expect(page.getByText(title).locator('visible=true').first()).toBeVisible()
}

export async function openSettings(page: Page, tab: string) {
  await page.locator('a[href="/settings"]').first().click()
  await page.getByTestId(`settings-tab-${tab}`).click()
}

export async function createFolder(page: Page, name: string) {
  await openSettings(page, 'organize')
  await page.getByRole('button', { name: 'New folder', exact: true }).click()
  await page.getByPlaceholder('Folder name').fill(name)
  await page.getByRole('button', { name: 'Create', exact: true }).click()
  await expect(page.getByText(name, { exact: true }).first()).toBeVisible()
}

export async function createRule(page: Page, name: string, subjectContains: string, folder: string) {
  await openSettings(page, 'filters')
  await page.getByRole('button', { name: 'New rule', exact: true }).click()
  const editor = page.getByRole('dialog', { name: 'New rule' })
  await expect(editor).toBeVisible()
  await editor.getByLabel('Condition 1', { exact: true }).selectOption({ label: 'Subject' })
  await editor.getByLabel('Condition value', { exact: true }).fill(subjectContains)
  await editor.getByRole('button', { name: 'Select folder', exact: true }).first().click()
  await page.getByRole('menuitem').filter({ hasText: folder }).first().click()
  await expect(editor.getByLabel('Move to folder', { exact: true })).toBeChecked()
  await editor.getByLabel('Rule name', { exact: true }).fill(name)
  await editor.getByRole('button', { name: 'Save', exact: true }).click()
  await expect(editor).toBeHidden()
  await expect(page.getByText(name, { exact: true }).first()).toBeVisible()
}

export async function backToMail(page: Page) {
  await page.getByRole('button', { name: 'Back to mail', exact: true }).click()
  await expect(page.getByTestId('folder-row').first()).toBeVisible()
}

export async function openWebmailAdmin(page: Page) {
  await page.getByRole('link', { name: 'Admin', exact: true }).click()
  await expect(page.getByRole('heading', { name: 'Overview' })).toBeVisible()
}

export async function openMailSettings(page: Page, user: string, password: string): Promise<Page> {
  const [server] = await Promise.all([
    page.context().waitForEvent('page'),
    page.getByRole('button', { name: 'Mail settings', exact: true }).click(),
  ])
  await server.locator('#username').fill(user)
  await server.getByRole('button', { name: 'Continue' }).click()
  await server.locator('input[type=password]').fill(password)
  await server.locator('button[type=submit]').click()
  return server
}
