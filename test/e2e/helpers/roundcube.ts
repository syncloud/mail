import { Page, expect } from '@playwright/test'

export async function login(page: Page, user: string, password: string) {
  await page.locator('#rcmloginuser').fill(user)
  await page.locator('#rcmloginpwd').fill(password)
  await page.locator('#rcmloginsubmit').click()
  await expect(page.locator('#messagelist')).toBeVisible()
}

export async function addContact(page: Page, firstName: string, lastName: string, email: string) {
  await page.locator('#taskmenu a.contacts').click()
  await expect(page.locator('#rcmcountdisplay')).not.toBeEmpty()
  const form = page.frameLocator('#contact-frame')
  await expect(async () => {
    await page.locator('a.create:visible').click()
    await expect(form.locator('#ff_firstname')).toBeVisible({ timeout: 5000 })
  }).toPass({ timeout: 60_000 })
  await form.locator('#ff_firstname').fill(firstName)
  await form.locator('#ff_surname').fill(lastName)
  await form.locator('#ff_email0').fill(email)
  await form.locator('button.submit').click()
  await expect(page.locator('#contacts-table')).toContainText(`${firstName} ${lastName}`)
}
