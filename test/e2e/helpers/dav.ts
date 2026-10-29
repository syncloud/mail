import { APIRequestContext, expect } from '@playwright/test'

export async function expectInCollection(request: APIRequestContext, href: string, user: string, password: string, text: string) {
  await expect(async () => {
    const response = await request.fetch(href, {
      method: 'PROPFIND',
      headers: {
        Authorization: `Basic ${Buffer.from(`${user}:${password}`).toString('base64')}`,
        Depth: '1',
        'Content-Type': 'application/xml',
      },
      data: '<?xml version="1.0"?><d:propfind xmlns:d="DAV:" xmlns:c="urn:ietf:params:xml:ns:carddav" xmlns:cal="urn:ietf:params:xml:ns:caldav"><d:prop><c:address-data/><cal:calendar-data/></d:prop></d:propfind>',
    })
    expect(response.status()).toBe(207)
    expect(await response.text()).toContain(text)
  }).toPass({ timeout: 30_000 })
}
