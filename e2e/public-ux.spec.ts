import {expect,test,type Page} from '@playwright/test'

const pageErrors=new WeakMap<Page,string[]>()
test.beforeEach(async({page})=>{
  const errors:string[]=[]
  pageErrors.set(page,errors)
  page.on('pageerror',error=>errors.push(error.name))
})
test.afterEach(async({page})=>{
  // Report only error classes, never submitted values or raw provider output.
  expect(pageErrors.get(page)||[],'Unexpected browser JavaScript exceptions').toEqual([])
})

test('route entry carries locations into the real requirement form',async({page})=>{
  await page.goto('/')
  await page.getByLabel('Pickup location',{exact:true}).fill('Pune')
  await page.getByLabel('Drop location',{exact:true}).fill('Mumbai')
  await page.getByRole('button',{name:'Get transport quotes',exact:true}).click()
  const dialog=page.getByRole('dialog')
  await expect(dialog).toBeVisible()
  await expect(dialog.getByLabel('Pickup location',{exact:true})).toHaveValue('Pune')
  await expect(dialog.getByLabel('Destination',{exact:true})).toHaveValue('Mumbai')
  await expect(dialog.getByRole('button',{name:'Fill form for me'})).toHaveCount(0)
})

test('an explicitly blank homepage route does not reuse unrelated draft locations',async({page})=>{
  await page.addInitScript(()=>localStorage.setItem('transivox_request_draft',JSON.stringify({pickup:'Old draft pickup',destination:'Old draft destination'})))
  await page.goto('/')
  await page.getByLabel('Pickup location',{exact:true}).fill('Pune')
  await page.getByRole('button',{name:'Get transport quotes',exact:true}).click()
  const dialog=page.getByRole('dialog')
  await expect(dialog.getByLabel('Destination',{exact:true})).toHaveValue('')
})

test('published requirement shows server reference and keeps success keyboard-contained',async({page})=>{
  await page.route('**/api/v1/requests',route=>route.request().method()==='POST'?route.fulfill({status:201,json:{id:'00000000-0000-4000-8000-000000000003',public_id:'UX-REAL-RESPONSE-123',status:'published'}}):route.fulfill({json:[]}))
  await page.goto('/')
  // Only the external API boundary is fake. The wizard and payload path are real.
  await page.evaluate(()=>sessionStorage.setItem('transivox_access_token','fictional-ux-customer'))
  await page.getByLabel('Pickup location',{exact:true}).fill('Pune')
  await page.getByLabel('Drop location',{exact:true}).fill('Mumbai')
  await page.getByRole('button',{name:'Get transport quotes',exact:true}).click()
  const dialog=page.getByRole('dialog')
  await dialog.getByRole('button',{name:'Transport now',exact:true}).click()
  await dialog.getByRole('button',{name:'Continue',exact:true}).click()
  await dialog.getByLabel('Brief description').fill('NOT A REAL SHIPMENT: harmless test cartons')
  await dialog.getByLabel('Total weight',{exact:true}).fill('1')
  await dialog.getByLabel('Number of parcels / packages').fill('1')
  for(const dimension of ['Length (m)','Width (m)','Height (m)'])await dialog.getByLabel(dimension,{exact:true}).fill('1')
  await dialog.getByRole('button',{name:'Continue',exact:true}).click()
  await dialog.getByRole('button',{name:'Continue',exact:true}).click()
  await dialog.getByRole('button',{name:'Publish requirement',exact:true}).click()
  await expect(page.getByText('UX-REAL-RESPONSE-123',{exact:false})).toBeVisible()
  await expect(page.getByRole('dialog',{name:'Your requirement is live'})).toBeVisible()
  await expect(page.getByRole('button',{name:'Done',exact:true})).toBeFocused()
  await page.keyboard.press('Tab')
  await expect(page.getByRole('button',{name:'Done',exact:true})).toBeFocused()
  await page.keyboard.press('Escape')
  await expect(page.getByRole('dialog')).toHaveCount(0)
})

test('sign-in failure preserves email, clears password and traps keyboard focus',async({page})=>{
  await page.route('**/auth/session/login',route=>route.abort('failed'))
  await page.goto('/')
  const opener=page.getByRole('button',{name:'Sign in',exact:true})
  await opener.click()
  const dialog=page.getByRole('dialog',{name:'Welcome back'})
  await expect(dialog).toBeVisible()
  await dialog.getByLabel('Email address',{exact:true}).fill('ux.e2e@example.com')
  await dialog.getByLabel('Password',{exact:true}).fill('NotARealPassword123')
  await dialog.locator('form').getByRole('button',{name:'Sign in',exact:true}).click()
  await expect(dialog.getByRole('alert')).toContainText('Check your connection')
  await expect(dialog.getByLabel('Email address',{exact:true})).toHaveValue('ux.e2e@example.com')
  await expect(dialog.getByLabel('Password',{exact:true})).toHaveValue('')
  await dialog.getByRole('button',{name:'Close sign in'}).focus()
  await page.keyboard.press('Shift+Tab')
  expect(await dialog.evaluate(element=>element.contains(document.activeElement))).toBe(true)
  await page.keyboard.press('Escape')
  await expect(dialog).toHaveCount(0)
  await expect(opener).toBeFocused()
})

test('new requirements do not start with a fabricated shipment',async({page})=>{
  await page.goto('/')
  await page.getByRole('navigation',{name:'Main navigation'}).getByRole('link',{name:'Ship goods',exact:true}).click()
  const dialog=page.getByRole('dialog')
  await expect(dialog.getByLabel('Pickup location',{exact:true})).toHaveValue('')
  await expect(dialog.getByLabel('Destination',{exact:true})).toHaveValue('')
  await dialog.getByRole('button',{name:'Continue',exact:true}).click()
  await expect(dialog.getByRole('alert')).toContainText('Enter both pickup and destination')
})

test('admin review queue remains reachable on mobile',async({page})=>{
  await page.setViewportSize({width:390,height:844})
  await page.addInitScript(()=>sessionStorage.setItem('transivox_access_token','fictional-ux-session'))
  await page.route('**/api/v1/**',route=>{
    const path=new URL(route.request().url()).pathname
    if(path.endsWith('/auth/me'))return route.fulfill({json:{id:'00000000-0000-4000-8000-000000000001',email:'ux.admin@example.com',full_name:'Fictional admin',roles:['admin'],status:'active',mobile:null,mobile_verified:false,email_verified:true}})
    if(path.endsWith('/admin/marketplace-health'))return route.fulfill({json:{verified_providers:0,approved_vehicles:0,open_requests:0,active_quotes:0,active_bookings:0,open_disputes:0,pending_kyc:1,gmv:'0',total_bookings:0,completed_bookings:0,completion_rate:0}})
    if(path.endsWith('/admin/analytics/funnel'))return route.fulfill({json:{period_days:30,funnel:[]}})
    if(path.endsWith('/admin/users'))return route.fulfill({json:{items:[],page:1,page_size:20,total:0}})
    if(path.includes('/kyc/admin/'))return route.fulfill({json:[]})
    return route.fulfill({status:503,json:{detail:'Unavailable test boundary'}})
  })
  await page.goto('/')
  await expect(page.getByRole('heading',{name:'Marketplace control centre'})).toBeVisible()
  await expect(page.getByRole('button',{name:'Open queue',exact:true})).toBeVisible()
  await page.getByRole('button',{name:'Review now',exact:true}).click()
  await expect(page.getByRole('heading',{name:'Verification review queue'})).toBeVisible()
  expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true)
})

for(const width of [360,768,1280])test(`public navigation and forms fit ${width}px`,async({page})=>{
  await page.setViewportSize({width,height:900})
  await page.goto('/')
  expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true)
  await expect(page.getByText('Current loads are unavailable.',{exact:true})).toBeVisible()
  await page.screenshot({path:`test-results/ui-after-home-${width}.png`,fullPage:true})
  await page.getByRole('button',{name:'Sign in',exact:true}).click()
  const dialog=page.getByRole('dialog',{name:'Welcome back'})
  await expect(dialog).toBeVisible()
  expect(await dialog.evaluate(element=>element.scrollWidth<=element.clientWidth)).toBe(true)
  await page.screenshot({path:`test-results/ui-after-sign-in-${width}.png`,fullPage:true})
})

test('provider application creation prevents duplicate requests and preserves a recoverable form',async({page})=>{
  let calls=0
  let release:()=>void=()=>{}
  const gate=new Promise<void>(resolve=>{release=resolve})
  await page.addInitScript(()=>sessionStorage.setItem('transivox_access_token','fictional-ux-provider'))
  await page.route('**/api/v1/**',async route=>{
    const path=new URL(route.request().url()).pathname
    if(path.endsWith('/auth/me'))return route.fulfill({json:{id:'00000000-0000-4000-8000-000000000002',full_name:'Fictional provider',email:'ux.provider@example.com',roles:['provider'],status:'active',mobile:null,mobile_verified:false,email_verified:true}})
    if(path.endsWith('/dashboard/summary'))return route.fulfill({json:{roles:['provider'],open_requests:0,active_quotes:0,active_bookings:0,active_trips:0,completed_bookings:0,total_booking_value:'0',provider_rating:null,provider_kyc_status:null}})
    if(path.endsWith('/kyc/applications/me'))return route.fulfill({status:404,json:{detail:'No application'}})
    if(path.endsWith('/kyc/applications')&&route.request().method()==='POST'){
      calls++;await gate;return route.fulfill({status:503,json:{detail:'Please try again later.'}})
    }
    return route.fulfill({status:503,json:{detail:'Unavailable test boundary'}})
  })
  await page.goto('/')
  await page.getByRole('button',{name:'Verification status',exact:true}).click()
  await page.getByLabel('Legal name',{exact:true}).fill('NOT A REAL TRANSPORT PROVIDER')
  const submit=page.getByRole('button',{name:'Create application',exact:true})
  await submit.click()
  await expect(page.locator('.kyc-create button')).toBeDisabled()
  release()
  await expect(page.getByRole('status')).toContainText('Please try again later.')
  await expect(page.getByLabel('Legal name',{exact:true})).toHaveValue('NOT A REAL TRANSPORT PROVIDER')
  expect(calls).toBe(1)
})
