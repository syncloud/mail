import { test, expect } from '@playwright/test'
import { shoot } from '../helpers/screenshot'

test.describe('mail admin relay', () => {
  test('configure outbound relay', async ({ page }, testInfo) => {
    await page.goto('/admin/')
    await expect(page.getByTestId('admin-title')).toBeVisible()
    await shoot(page, testInfo, 'admin')

    await page.getByTestId('relay-enabled').click()
    await page.getByTestId('relay-host').locator('input').fill('smtp.gmail.com')
    await page.getByTestId('relay-port').locator('input').fill('587')
    await page.getByTestId('relay-user').locator('input').fill('user@gmail.com')
    await page.getByTestId('relay-password').locator('input').fill('app-password')
    await shoot(page, testInfo, 'relay-filled')

    await page.getByTestId('relay-save').click()
    await expect(page.getByText('Saved')).toBeVisible()
    await shoot(page, testInfo, 'relay-saved')
  })
})
