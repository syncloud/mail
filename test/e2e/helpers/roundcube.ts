import { Page, expect } from '@playwright/test'

export async function login(page: Page, user: string, password: string) {
  await page.locator('#rcmloginuser').fill(user)
  await page.locator('#rcmloginpwd').fill(password)
  await page.locator('#rcmloginsubmit').click()
}

export async function expectInbox(page: Page) {
  await expect(page.locator('#messagelist')).toBeVisible()
}

export async function compose(page: Page, to: string, subject: string, body: string) {
  await page.locator('a.compose:visible').first().click()
  await expect(page.locator('#composebody')).toBeVisible()
  await page.locator('#_to').fill(to)
  await page.keyboard.press('Tab')
  await page.locator('#compose-subject').fill(subject)
  await page.locator('#composebody').fill(body)
  await page.locator('.send.btn-primary:visible').first().click()
}

export async function expectInboxContains(page: Page, subject: string) {
  await expect(async () => {
    await page.locator('a[rel="INBOX"]:visible').first().click({ timeout: 3000 }).catch(() => {})
    await expect(page.locator('#messagelist')).toContainText(subject, { timeout: 3000 })
  }).toPass({ timeout: 45000 })
}
