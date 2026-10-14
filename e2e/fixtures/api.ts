import {expect, type Page} from '@playwright/test'

// Never include bodies, headers, query strings, tokens or personal input in
// diagnostics. Status + route + validation field/type identifies the failing API.
export function captureApiFailures(page: Page) {
  page.on('response', async response => {
    const url = new URL(response.url())
    if (!url.pathname.startsWith('/api/v1/') || response.status() < 400) return
    const payload = await response.json().catch(() => ({}))
    const validation = Array.isArray(payload.detail) ? payload.detail.map((item: {loc?:unknown[];type?:string}) => ({
      field: item.loc?.filter(value=>typeof value==='string'&&/^[a-z_]+$/.test(value)),
      type: typeof item.type==='string'&&/^[a-z_]+$/.test(item.type)?item.type:'validation_error',
    })) : undefined
    console.error('API failure (response values redacted):', JSON.stringify({method:response.request().method(),route:url.pathname.replace(/[0-9a-f]{8}-[0-9a-f-]{27,}/gi,':id'),status:response.status(),validation}))
  })
}

export async function signIn(page: Page, email: string, password: string) {
  await page.goto('/')
  await page.getByRole('button', {name: 'Sign in', exact: true}).click()
  await page.getByLabel('Email address').fill(email)
  await page.getByLabel('Password').fill(password)
  const login = page.waitForResponse(response => new URL(response.url()).pathname.endsWith('/auth/login') && response.request().method()==='POST')
  await page.getByRole('button', {name: /Sign in securely/}).click()
  const result = await login
  if(!result.ok())throw new Error(`Login API failed with HTTP ${result.status()} (response values redacted)`)
  const {user}=await result.json()
  const roles:string[]=user.roles
  const heading=roles.some(role=>['admin','superadmin'].includes(role))?'Marketplace control centre'
    :roles.some(role=>['provider','fleet_owner'].includes(role))?'Provider dashboard'
    :roles.includes('driver')?'Trip operations':'Customer dashboard'
  await page.getByRole('heading', {name: heading, exact:true}).waitFor()
}

export async function accessToken(page: Page): Promise<string> {
  return page.evaluate(() => sessionStorage.getItem('transivox_access_token') || '')
}

export async function reloadProviderDashboard(page:Page) {
  await page.reload()
  // The avatar appears only after /auth/me restores the authenticated user.
  await expect(page.locator('header .avatar')).toBeVisible()
  await page.locator('header .avatar').click()
  await expect(page.getByRole('heading',{name:'Provider dashboard',exact:true})).toBeVisible()
  await expect(page.getByRole('button',{name:'Verification status',exact:true})).toBeVisible()
}
