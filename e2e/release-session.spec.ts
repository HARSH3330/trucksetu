import {expect,test,type Page} from '@playwright/test'
import {spawnSync} from 'node:child_process'
import path from 'node:path'
import {providerAccount,adminAccount} from './fixtures/accounts'
import {accessToken,blockExternalFonts,captureApiFailures,signIn} from './fixtures/api'

const api=(process.env.E2E_API_URL||'http://127.0.0.1:8000/api/v1').replace(/\/$/,'')
const origin=new URL(process.env.E2E_WEB_URL||'http://127.0.0.1:5173').origin

async function invalidate(page:Page,action:'expire'|'revoke'){
  const token=await accessToken(page)
  const response=await page.request.get(`${api}/auth/me`,{headers:{Authorization:`Bearer ${token}`}})
  expect(response.status()).toBe(200)
  const {id}=await response.json()
  const result=spawnSync(process.env.E2E_PYTHON||'python',['-m','e2e_session_control',action,id],{cwd:path.resolve('backend'),env:process.env,stdio:'pipe'})
  expect(result.status,'Guarded local session fixture (details redacted)').toBe(0)
  await page.evaluate(()=>sessionStorage.removeItem('transivox_access_token'))
  await page.reload()
  await expect(page.locator('header').getByRole('button',{name:'Sign in',exact:true})).toBeVisible()
  await expect(page.locator('header .avatar')).toHaveCount(0)
}

test('real PostgreSQL session survives browser reopening, refreshes, enforces CSRF and revokes on logout',async({browser,request})=>{
  const first=await browser.newContext()
  let reopened:Awaited<ReturnType<typeof browser.newContext>>|undefined
  try{
    const page=await first.newPage();captureApiFailures(page)
    await signIn(page,providerAccount.email,providerAccount.password)
    const cookies=await first.cookies(api+'/auth/session/refresh')
    const cookie=cookies.find(item=>item.name==='transivox_refresh')
    expect(cookie?.httpOnly).toBe(true)
    expect(cookie!.expires).toBeGreaterThan(Date.now()/1000)
    const persisted=await first.storageState()
    await first.close()
    reopened=await browser.newContext({storageState:persisted})
    const restored=await reopened.newPage();captureApiFailures(restored);await blockExternalFonts(restored)
    await restored.goto('/')
    await expect(restored.getByRole('heading',{name:'Provider dashboard',exact:true})).toBeVisible()
    await restored.reload()
    await expect(restored.locator('header .avatar')).toBeVisible()
    expect(await restored.evaluate(()=>sessionStorage.getItem('transivox_refresh_token'))).toBeNull()
    // Force an invalid access credential: the real API must rotate the cookie.
    await restored.evaluate(()=>sessionStorage.setItem('transivox_access_token','expired-fictional-token'))
    await restored.reload()
    await expect(restored.locator('header .avatar')).toBeVisible()
    expect((await restored.request.post(`${api}/auth/session/refresh`,{headers:{Origin:origin}})).status()).toBe(403)
    expect((await restored.request.post(`${api}/auth/session/refresh`,{headers:{Origin:'https://attacker.invalid','X-TransivoX-CSRF':'1'}})).status()).toBe(403)
    expect((await request.get(`${api}/auth/me`)).status()).toBe(401)
    const beforeLogout=(await reopened.cookies(api+'/auth/session/refresh')).find(item=>item.name==='transivox_refresh')!
    await restored.getByRole('button',{name:'Sign out',exact:true}).click()
    await expect(restored.getByText('Signed out.',{exact:true})).toBeVisible()
    expect((await reopened.cookies()).some(item=>item.name==='transivox_refresh')).toBe(false)
    expect((await request.post(`${api}/auth/session/refresh`,{headers:{Origin:origin,'X-TransivoX-CSRF':'1',Cookie:`transivox_refresh=${beforeLogout.value}`}})).status()).toBe(401)
    await restored.reload()
    await expect(restored.locator('header .avatar')).toHaveCount(0)
  }finally{if(reopened)await reopened.close();else await first.close()}
})

test('real session expiry and revocation deny restoration without mixing provider and admin accounts',async({browser})=>{
  const provider=await browser.newContext(),admin=await browser.newContext()
  try{
    const p=await provider.newPage(),a=await admin.newPage()
    captureApiFailures(p);captureApiFailures(a)
    await signIn(p,providerAccount.email,providerAccount.password)
    await signIn(a,adminAccount.email,adminAccount.password)
    const identities=await Promise.all([p,a].map(async page=>{
      const response=await page.request.get(`${api}/auth/me`,{headers:{Authorization:`Bearer ${await accessToken(page)}`}})
      expect(response.status()).toBe(200);return response.json()
    }))
    expect(identities[0].id).not.toBe(identities[1].id)
    expect(identities[0].roles).toContain('provider');expect(identities[1].roles).toContain('admin')
    await invalidate(p,'expire')
    await a.reload()
    await expect(a.locator('header .avatar')).toBeVisible()
    await signIn(p,providerAccount.email,providerAccount.password)
    await invalidate(p,'revoke')
  }finally{await provider.close();await admin.close()}
})
