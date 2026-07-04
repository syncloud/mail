import { Page, expect } from '@playwright/test'

export async function login(page: Page, user: string, password: string) {
  await page.locator('#rcmloginuser').fill(user)
  await page.locator('#rcmloginpwd').fill(password)
  await page.locator('#rcmloginsubmit').click()
}

export async function expectInbox(page: Page) {
  await expect(page.locator('#messagelist')).toBeVisible()
}
