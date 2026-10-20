import {expect,test,type BrowserContext} from '@playwright/test'

// Real application UI and session client, synthetic HTTP boundary only.
// PostgreSQL rotation/revocation is covered separately, not proved here.
async function boundary(context:BrowserContext,valid=true){
  let active=valid
  await context.route('**/api/v1/**',async route=>{
    const path=new URL(route.request().url()).pathname
    if(path.endsWith('/auth/session/refresh')){
      expect(route.request().headers()['x-transivox-csrf']).toBe('1')
      const cookie=route.request().headers().cookie||''
      return active&&cookie.includes('transivox_refresh=fictional-persistent-session')
        ?route.fulfill({json:{access_token:'fictional-restored-access'}})
        :route.fulfill({status:401,json:{detail:'Session expired'}})
    }
    if(path.endsWith('/auth/session/logout')){active=false;return route.fulfill({status:204,headers:{'set-cookie':'transivox_refresh=; Path=/api/v1/auth/session; Max-Age=0; HttpOnly; SameSite=Lax'}})}
    if(path.endsWith('/auth/me'))return route.fulfill({json:{id:'fictional-persistent-provider',full_name:'Fictional provider',email:'provider.e2e@example.com',roles:['provider']}})
    if(path.endsWith('/providers/me'))return route.fulfill({json:{id:'fictional-provider',provider_type:'owner',kyc_status:'registered'}})
    if(path.endsWith('/dashboard/summary'))return route.fulfill({json:{roles:['provider'],open_requests:0,active_quotes:0,active_bookings:0,active_trips:0,completed_bookings:0,total_booking_value:'0',provider_rating:null,provider_kyc_status:'registered'}})
    return route.fulfill({json:[]})
  })
}

test('reopened browser context restores role using a persistent cookie, then logout clears it',async({browser})=>{
  const first=await browser.newContext()
  await first.addCookies([{name:'transivox_refresh',value:'fictional-persistent-session',domain:'127.0.0.1',path:'/api/v1/auth/session',httpOnly:true,secure:false,sameSite:'Lax',expires:Math.floor(Date.now()/1000)+3600}])
  const persisted=await first.storageState()
  await first.close()
  const reopened=await browser.newContext({storageState:persisted})
  try{
    await boundary(reopened)
    const page=await reopened.newPage()
    await page.goto('/')
    await expect(page.locator('header .avatar')).toBeVisible()
    expect(await page.evaluate(()=>sessionStorage.getItem('transivox_refresh_token'))).toBeNull()
    await page.reload()
    await expect(page.locator('header .avatar')).toBeVisible()
    await page.getByRole('button',{name:'Sign out',exact:true}).click()
    await expect(page.getByText('Signed out.',{exact:true})).toBeVisible()
    expect((await reopened.cookies()).some(cookie=>cookie.name==='transivox_refresh')).toBe(false)
    await page.reload()
    await expect(page.getByRole('button',{name:'Sign in',exact:true})).toBeVisible()
    await expect(page.locator('header .avatar')).toHaveCount(0)
  }finally{await reopened.close()}
})

test('expired cookie does not render a protected account or lose the intended destination',async({context,page})=>{
  await boundary(context,false)
  await page.goto('/#bookings')
  await expect(page.locator('header').getByRole('button',{name:'Sign in',exact:true})).toBeVisible()
  await expect(page.locator('header .avatar')).toHaveCount(0)
  await expect(page).toHaveURL(/#bookings$/)
  await expect(page.getByText('Restoring your session…',{exact:true})).toHaveCount(0)
})
