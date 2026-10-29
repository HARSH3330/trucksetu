import {expect,test} from '@playwright/test'

const pendingByPage = new WeakMap<object,Set<string>>()
test.afterEach(async({page},testInfo)=>{
  if(testInfo.status!==testInfo.expectedStatus)await testInfo.attach('pending-request-paths',{body:JSON.stringify([...pendingByPage.get(page)||[]]),contentType:'application/json'})
})

test('provider sees needs-documents explanation and private upload path',async({page})=>{
  const pending=new Set<string>()
  pendingByPage.set(page,pending)
  page.on('request',request=>{const url=new URL(request.url());pending.add(url.origin+url.pathname)})
  page.on('requestfinished',request=>{const url=new URL(request.url());pending.delete(url.origin+url.pathname)})
  page.on('requestfailed',request=>{const url=new URL(request.url());pending.delete(url.origin+url.pathname)})
  await page.addInitScript(()=>sessionStorage.setItem('transivox_access_token','fictional-access'))
  await page.route('**/api/v1/**',route=>{
    const path=new URL(route.request().url()).pathname
    if(path.endsWith('/auth/me'))return route.fulfill({json:{id:'fictional-owner',full_name:'Fictional owner',email:'provider.e2e@example.com',roles:['provider']}})
    if(path.endsWith('/providers/me'))return route.fulfill({json:{id:'fictional-provider',display_name:'Fictional provider',provider_type:'owner',kyc_status:'verified',active:true}})
    if(path.endsWith('/carrier-vehicles'))return route.fulfill({json:[{id:'fictional-vehicle',vehicle_category_name:'Fictional truck',registration_number:'NOT-REAL',body_type:'closed',maximum_payload_tonnes:'10',maximum_volume_m3:'20',permit_territories:['Delhi'],service_areas:['Delhi'],status:'pending',document_eligible_today:false,document_review_state:'needs_documents',missing_accepted_documents:['rc','insurance','fitness','pollution','permit'],document_expiries:{rc:'2030-01-01'}}]})
    if(path.endsWith('/drivers')||path.endsWith('/vehicle-categories')||path.endsWith('/documents'))return route.fulfill({json:[]})
    return route.fulfill({status:404,json:{detail:'Unknown harmless test boundary'}})
  })
  await page.goto('/#fleet')
  await expect(page.getByText('Documents required before new assignments',{exact:true})).toBeVisible()
  await page.getByText('Private documents',{exact:true}).click()
  await expect(page.getByRole('button',{name:'Upload private document',exact:true})).toBeVisible()
  await page.setViewportSize({width:390,height:844})
  expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true)
})

test('admin driver reactivation requires a separate reasoned review',async({page})=>{
  await page.addInitScript(()=>sessionStorage.setItem('transivox_access_token','fictional-access'))
  let restored=false
  await page.route('**/api/v1/**',route=>{
    const path=new URL(route.request().url()).pathname
    if(path.endsWith('/auth/me'))return route.fulfill({json:{id:'fictional-admin',full_name:'Fictional admin',email:'admin.e2e@example.com',roles:['admin']}})
    if(path.endsWith('/marketplace-health'))return route.fulfill({json:{verified_providers:0,approved_vehicles:0,open_requests:0,active_quotes:0,active_bookings:0,open_disputes:0,pending_kyc:0,gmv:'0',total_bookings:0,completed_bookings:0,completion_rate:0}})
    if(path.endsWith('/analytics/funnel'))return route.fulfill({json:{period_days:30,funnel:[]}})
    if(path.endsWith('/admin/users'))return route.fulfill({json:{items:[{id:'fictional-driver-user',name:'Fictional driver',email:'driver.e2e@example.com',roles:['driver'],status:'active',email_verified:true}],page:1,page_size:25,total:1}})
    if(path.endsWith('/driver-reactivation')){expect(route.request().postDataJSON().reason).toBe('Harmless fixture: current records reviewed.');restored=true;return route.fulfill({json:{id:'fictional-driver',active:true,kyc_status:'verified'}})}
    return route.fulfill({status:404,json:{detail:'Unknown test boundary'}})
  })
  await page.goto('/#admin')
  await page.getByRole('button',{name:'Review driver reactivation',exact:true}).click()
  await page.getByLabel('Driver review reason',{exact:true}).fill('Harmless fixture: current records reviewed.')
  await page.getByRole('button',{name:'Confirm driver reactivation',exact:true}).click()
  await expect(page.getByText('Driver eligibility restored after server-side identity, licence and scan checks.',{exact:true})).toBeVisible()
  expect(restored).toBe(true)
})

test('admin can request re-verification for a previously verified application',async({page})=>{
  await page.addInitScript(()=>sessionStorage.setItem('transivox_access_token','fictional-access'))
  let decision=false
  await page.route('**/api/v1/**',route=>{
    const path=new URL(route.request().url()).pathname
    if(path.endsWith('/auth/me'))return route.fulfill({json:{id:'fictional-admin',full_name:'Fictional admin',email:'admin.e2e@example.com',roles:['admin']}})
    if(path.endsWith('/admin/applications'))return route.fulfill({json:new URL(route.request().url()).searchParams.get('status')==='verified'&&!decision?[{id:'fictional-application',provider_id:'fictional-provider',provider_name:'Fictional provider',provider_type:'owner',status:'verified',legal_name:'NOT A REAL IDENTITY',submitted_at:null,decision_reason:null,documents:[]}]:[]})
    if(path.endsWith('/expiring-documents'))return route.fulfill({json:[]})
    if(path.endsWith('/review')){expect(route.request().postDataJSON().decision).toBe('resubmit_required');decision=true;return route.fulfill({json:{status:'resubmit_required'}})}
    return route.fulfill({status:404,json:{detail:'Unknown test boundary'}})
  })
  await page.goto('/#kyc')
  await page.getByLabel('Application status filter').selectOption('verified')
  await page.getByLabel('Application decision').selectOption('resubmit_required')
  await page.getByLabel('Review reason').fill('Harmless test: please submit new version-pinned documents.')
  await page.getByRole('button',{name:'Record decision',exact:true}).click()
  await expect(page.getByText('Review decision recorded.',{exact:true})).toBeVisible()
  expect(decision).toBe(true)
})

test('provider publishes shared capacity using owned vehicle and driver references',async({page})=>{
  await page.addInitScript(()=>sessionStorage.setItem('transivox_access_token','fictional-access'))
  let published=false
  await page.route('**/api/v1/**',route=>{
    const path=new URL(route.request().url()).pathname
    if(path.endsWith('/auth/me'))return route.fulfill({json:{id:'fictional-provider-user',full_name:'Fictional provider',email:'provider.e2e@example.com',roles:['provider']}})
    if(path.endsWith('/providers/me'))return route.fulfill({json:{id:'fictional-provider',display_name:'NOT A REAL PROVIDER',provider_type:'owner',kyc_status:'verified',active:true}})
    if(path.endsWith('/carrier-vehicles'))return route.fulfill({json:[{id:'fictional-vehicle',vehicle_category_id:'fictional-category',registration_number:'NOT-REAL',status:'approved',document_eligible_today:true,maximum_payload_tonnes:'10',maximum_volume_m3:'20',permit_territories:['Delhi','Noida'],service_areas:['Delhi']}]})
    if(path.endsWith('/drivers'))return route.fulfill({json:[{id:'fictional-driver',full_name:'Fictional driver',active:true,kyc_status:'verified'}]})
    if(path.endsWith('/available-routes')&&route.request().method()==='POST'){
      const body=route.request().postDataJSON();expect(body.provider_id).toBe('fictional-provider');expect(body.carrier_vehicle_id).toBe('fictional-vehicle');expect(body.driver_id).toBe('fictional-driver');expect(body.available_capacity_tonnes).toBe('2');expect(body.allowed_cargo_types).toEqual(['Furniture'])
      published=true;return route.fulfill({status:201,json:{id:'fictional-route'}})
    }
    return route.fulfill({status:404,json:{detail:'Unknown test boundary'}})
  })
  await page.goto('/#capacity')
  await page.getByText('Publish shared capacity',{exact:true}).click()
  const form=page.getByRole('form',{name:'Publish shared capacity'})
  for(const [label,value] of Object.entries({'Route origin city':'Delhi','Route destination city':'Noida','Route origin address':'Fictional pickup depot','Route destination address':'Fictional delivery depot','Departure start':'2030-01-01T10:00','Departure window end':'2030-01-01T11:00','Expected arrival':'2030-01-01T14:00','Total weight capacity (tonnes)':'10','Available weight (tonnes)':'2','Total volume (m³)':'20','Available volume (m³)':'4','Minimum booking weight (tonnes)':'1','Allowed cargo types':'Furniture','Route price (INR)':'1000','Minimum acceptable earning (INR)':'500','Maximum deviation (km)':'10','Maximum added time (minutes)':'60'}))await form.getByLabel(label,{exact:true}).fill(value)
  await form.getByRole('button',{name:'Publish route',exact:true}).click()
  await expect(page.getByText('Published route fictional-route',{exact:true})).toBeVisible()
  expect(published).toBe(true)
})

test('admin records an externally completed refund with explicit confirmation',async({page})=>{
  await page.addInitScript(()=>sessionStorage.setItem('transivox_access_token','fictional-access'))
  let submitted=false
  await page.route('**/api/v1/**',route=>{
    const path=new URL(route.request().url()).pathname
    if(path.endsWith('/auth/me'))return route.fulfill({json:{id:'fictional-admin',full_name:'Fictional admin',email:'admin.e2e@example.com',roles:['admin']}})
    if(path.endsWith('/payments'))return route.fulfill({json:[]})
    if(path.endsWith('/admin/refunds'))return route.fulfill({json:submitted?[]:[{booking_id:'fictional-booking',booking_public_id:'TEST-BOOKING',approved_amount:'1000',processed_amount:'300',remaining_amount:'700'}]})
    if(path.endsWith('/refunds/manual')){
      const body=route.request().postDataJSON()
      expect(body.amount).toBe('700');expect(body.method).toBe('bank_transfer');expect(body.reference).toBe('NOT-A-REAL-TRANSFER');expect(body.idempotency_key.length).toBeGreaterThan(12)
      submitted=true;return route.fulfill({status:201,json:{refund_id:'fictional-refund',status:'processed',amount:'700'}})
    }
    return route.fulfill({status:404,json:{detail:'Unknown test boundary'}})
  })
  await page.goto('/#payments')
  const panel=page.getByRole('region',{name:'Manual refund records'})
  await panel.getByLabel('Refund reference',{exact:true}).fill('NOT-A-REAL-TRANSFER')
  const submit=panel.getByRole('button',{name:'Record completed refund',exact:true})
  await expect(submit).toBeDisabled()
  await panel.getByLabel('I confirm this refund was completed outside TransivoX.').check()
  await submit.click()
  await expect(panel.getByText('No approved refunds awaiting recording.',{exact:true})).toBeVisible()
  expect(submitted).toBe(true)
})

test('issued invoice record downloads through the authorized API on mobile',async({page})=>{
  await page.addInitScript(()=>sessionStorage.setItem('transivox_access_token','fictional-access'))
  await page.setViewportSize({width:390,height:844})
  await page.route('**/api/v1/**',route=>{
    expect(route.request().headers().authorization).toBe('Bearer fictional-access')
    const path=new URL(route.request().url()).pathname
    if(path.endsWith('/auth/me'))return route.fulfill({json:{id:'fictional-customer',full_name:'Fictional customer',email:'test@example.com',roles:['customer']}})
    if(path.endsWith('/payments'))return route.fulfill({json:[]})
    if(path.endsWith('/invoices'))return route.fulfill({json:[{id:'fictional-invoice',booking_id:'fictional-booking',booking_public_id:'TEST-BOOKING',invoice_number:'TEST-INVOICE',legal_name:'NOT A REAL BUSINESS',gstin:null,billing_address:'Fictional test address',taxable_amount:'100.00',tax_percent:'18',tax_amount:'18.00',total_amount:'118.00',status:'issued',issued_at:'2026-10-14T00:00:00Z'}]})
    if(path.endsWith('/invoices/fictional-invoice/download'))return route.fulfill({json:{filename:'fictional-invoice.html',content_type:'text/html',content:'<!doctype html><title>NOT A REAL INVOICE</title>'}})
    return route.fulfill({status:404,json:{detail:'Unknown test boundary'}})
  })
  await page.goto('/#invoices')
  const download=page.waitForEvent('download')
  await page.getByRole('button',{name:'Download printable record',exact:true}).click()
  expect((await download).suggestedFilename()).toBe('fictional-invoice.html')
  expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true)
})

test('logout clears protected screens across browser Back and reload',async({page})=>{
  await page.addInitScript(()=>{
    if(!sessionStorage.getItem('logout-fixture-initialized')){
      sessionStorage.setItem('logout-fixture-initialized','true')
      sessionStorage.setItem('transivox_access_token','fictional-access')
      sessionStorage.setItem('transivox_refresh_token','fictional-refresh')
    }
  })
  await page.route('**/api/v1/**',route=>{
    const path=new URL(route.request().url()).pathname
    if(path.endsWith('/auth/session/migrate')){
      expect(route.request().postDataJSON()).toEqual({refresh_token:'fictional-refresh'})
      return route.fulfill({json:{access_token:'fictional-access'}})
    }
    if(path.endsWith('/auth/session/logout')){
      return route.fulfill({status:204})
    }
    if(!route.request().headers().authorization)return route.fulfill({status:401,json:{detail:'Sign in required'}})
    if(path.endsWith('/auth/me'))return route.fulfill({json:{id:'00000000-0000-4000-8000-000000000004',full_name:'Fictional customer',email:'ux.customer@example.com',roles:['customer']}})
    if(path.endsWith('/bookings'))return route.fulfill({json:[]})
    return route.fulfill({status:503,json:{detail:'Unavailable test boundary'}})
  })
  await page.goto('/#bookings')
  await expect(page.getByText('No bookings yet',{exact:true})).toBeVisible()
  await page.getByRole('button',{name:'Sign out',exact:true}).click()
  await expect(page.getByRole('button',{name:'Sign in',exact:true}).first()).toBeVisible()
  expect(await page.evaluate(()=>sessionStorage.getItem('transivox_refresh_token'))).toBeNull()
  await page.goBack()
  await expect(page.getByText('Sign in to view bookings',{exact:true})).toBeVisible()
  await page.reload()
  await expect(page.getByText('Sign in to view bookings',{exact:true})).toBeVisible()
  await page.setViewportSize({width:390,height:844})
  expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true)
})

test('public navigation has distinct URLs that survive reload and browser Back',async({page})=>{
  await page.goto('/')
  await page.getByRole('navigation',{name:'Main navigation'}).getByRole('link',{name:'Find loads',exact:true}).click()
  await expect(page).toHaveURL(/#loads$/)
  await page.reload()
  await expect(page.getByRole('heading',{name:'Find loads near you'})).toBeVisible()
  await page.getByRole('link',{name:'Shared truck space',exact:true}).first().click()
  await expect(page).toHaveURL(/#capacity$/)
  await page.goBack()
  await expect(page.getByRole('heading',{name:'Find loads near you'})).toBeVisible()
})

test('signed-out support and policies are public and do not expose private cases',async({page})=>{
  await page.route('**/legal/terms',route=>route.fulfill({json:{version:'fictional-test-version',content:'TEST TERMS NOT LEGAL ADVICE',status:'draft_pending_legal_review'}}))
  await page.goto('/#support')
  await expect(page.getByRole('heading',{name:'Safety & support',exact:true})).toBeVisible()
  await expect(page.getByRole('heading',{name:'What verification means'})).toBeVisible()
  await expect(page.getByRole('button',{name:'My bookings',exact:true})).toHaveCount(0)
  await page.getByRole('link',{name:'Terms & Conditions',exact:true}).first().click()
  await expect(page).toHaveURL(/#terms$/)
  await expect(page.getByText('TEST TERMS NOT LEGAL ADVICE',{exact:true})).toBeVisible()
})

test('filters open, apply and reset actual published API rows',async({page})=>{
  await page.route('**/api/v1/requests',route=>route.fulfill({json:[
    {id:'00000000-0000-4000-8000-000000000001',public_id:'TEST-LOAD-ONE',status:'published',pickup_address:'Pune',destination_address:'Mumbai',pickup_date:'2026-12-01',pickup_time:null,cargo_category:'Furniture',cargo_weight_tonnes:'5',vehicle_count:1,budget_amount:'10000'},
    {id:'00000000-0000-4000-8000-000000000002',public_id:'TEST-LOAD-TWO',status:'published',pickup_address:'Delhi',destination_address:'Jaipur',pickup_date:'2026-12-02',pickup_time:null,cargo_category:'Appliances',cargo_weight_tonnes:'12',vehicle_count:2,budget_amount:null},
  ]}))
  await page.goto('/#loads')
  await expect(page.locator('.load-card')).toHaveCount(2)
  await page.getByRole('button',{name:'Filters',exact:true}).click()
  const dialog=page.getByRole('dialog',{name:'Filter loads'})
  await expect(dialog).toBeVisible()
  await dialog.getByLabel('Cargo type',{exact:true}).selectOption('Furniture')
  await dialog.getByRole('button',{name:'Apply filters',exact:true}).click()
  await expect(page.locator('.load-card')).toHaveCount(1)
  await expect(page.getByText('TEST-LOAD-ONE',{exact:true})).toBeVisible()
  await page.getByRole('button',{name:'Filters (1)',exact:true}).click()
  await page.getByRole('button',{name:'Reset filters',exact:true}).click()
  await page.getByRole('button',{name:'Apply filters',exact:true}).click()
  await expect(page.locator('.load-card')).toHaveCount(2)
})

test('homepage load action opens the selected published requirement and survives reload',async({page})=>{
  await page.route('**/api/v1/requests',route=>route.fulfill({json:[
    {id:'00000000-0000-4000-8000-000000000001',public_id:'TEST-LOAD-ONE',status:'published',pickup_address:'Pune',destination_address:'Mumbai',pickup_date:'2026-12-01',pickup_time:null,cargo_category:'Furniture',cargo_weight_tonnes:'5',vehicle_count:1,budget_amount:'10000'},
    {id:'00000000-0000-4000-8000-000000000002',public_id:'TEST-LOAD-TWO',status:'published',pickup_address:'Delhi',destination_address:'Jaipur',pickup_date:'2026-12-02',pickup_time:null,cargo_category:'Appliances',cargo_weight_tonnes:'12',vehicle_count:2,budget_amount:null},
  ]}))
  await page.goto('/')
  await page.locator('.load-card').filter({hasText:'TEST-LOAD-TWO'}).getByRole('button',{name:'View load',exact:true}).click()
  await expect(page).toHaveURL(/#loads\?search=TEST-LOAD-TWO$/)
  await expect(page.locator('.load-card')).toHaveCount(1)
  await expect(page.getByText('TEST-LOAD-TWO',{exact:true})).toBeVisible()
  await page.reload()
  await expect(page.locator('.load-card')).toHaveCount(1)
  await expect(page.getByText('TEST-LOAD-TWO',{exact:true})).toBeVisible()
})

test('shipping route preserves entered details across refresh',async({page})=>{
  await page.goto('/')
  await page.getByLabel('Pickup location',{exact:true}).fill('Pune')
  await page.getByLabel('Drop location',{exact:true}).fill('Mumbai')
  await page.getByRole('button',{name:'Get transport quotes',exact:true}).click()
  await expect(page).toHaveURL(/#ship$/)
  await page.getByRole('dialog').getByLabel('Pickup location',{exact:true}).fill('Pune loading depot')
  await page.reload()
  await expect(page.getByRole('dialog').getByLabel('Pickup location',{exact:true})).toHaveValue('Pune loading depot')
  await expect(page.getByRole('dialog').getByLabel('Destination',{exact:true})).toHaveValue('Mumbai')
})

test('edited shipping details survive sign-in instead of reverting to homepage values',async({page})=>{
  await page.route('**/auth/session/login',route=>route.fulfill({json:{access_token:'fictional-ux-session',refresh_token:'fictional-ux-refresh',user:{id:'00000000-0000-4000-8000-000000000004',full_name:'Fictional customer',email:'ux.customer@example.com',roles:['customer']}}}))
  await page.goto('/')
  await page.getByLabel('Pickup location',{exact:true}).fill('Pune')
  await page.getByLabel('Drop location',{exact:true}).fill('Mumbai')
  await page.getByRole('button',{name:'Get transport quotes',exact:true}).click()
  const wizard=page.getByRole('dialog')
  await wizard.getByLabel('Destination',{exact:true}).fill('Delhi')
  await wizard.getByRole('button',{name:'Transport now',exact:true}).click()
  await wizard.getByRole('button',{name:'Continue',exact:true}).click()
  await wizard.getByLabel('Brief description').fill('NOT A REAL SHIPMENT: test cartons')
  await wizard.getByLabel('Total weight',{exact:true}).fill('1')
  await wizard.getByLabel('Number of parcels / packages').fill('1')
  for(const dimension of ['Length (m)','Width (m)','Height (m)'])await wizard.getByLabel(dimension,{exact:true}).fill('1')
  await wizard.getByRole('button',{name:'Continue',exact:true}).click()
  await wizard.getByRole('button',{name:'Continue',exact:true}).click()
  await wizard.getByRole('button',{name:'Publish requirement',exact:true}).click()
  await wizard.getByRole('button',{name:'Sign in to publish',exact:true}).click()
  const auth=page.getByRole('dialog',{name:'Welcome back'})
  await auth.getByLabel('Email address',{exact:true}).fill('ux.customer@example.com')
  await auth.getByLabel('Password',{exact:true}).fill('FictionalPassword123!')
  await auth.locator('form').getByRole('button',{name:'Sign in',exact:true}).click()
  await expect(page.getByRole('dialog').getByLabel('Destination',{exact:true})).toHaveValue('Delhi')
})

test('successful sign-in reloads the current private bookings screen',async({page})=>{
  await page.route('**/api/v1/**',route=>{
    const path=new URL(route.request().url()).pathname
    if(path.endsWith('/auth/session/login'))return route.fulfill({json:{access_token:'fictional-ux-session',refresh_token:'fictional-ux-refresh',user:{id:'00000000-0000-4000-8000-000000000004',full_name:'Fictional customer',email:'ux.customer@example.com',roles:['customer']}}})
    if(path.endsWith('/bookings'))return route.request().headers().authorization?route.fulfill({json:[]}):route.fulfill({status:401,json:{detail:'Sign in required'}})
    return route.fulfill({status:503,json:{detail:'Unavailable test boundary'}})
  })
  await page.goto('/#bookings')
  await expect(page.getByText('Sign in to view bookings',{exact:true})).toBeVisible()
  await page.getByRole('button',{name:'Sign in',exact:true}).first().click()
  const auth=page.getByRole('dialog',{name:'Welcome back'})
  await auth.getByLabel('Email address',{exact:true}).fill('ux.customer@example.com')
  await auth.getByLabel('Password',{exact:true}).fill('FictionalPassword123!')
  await auth.locator('form').getByRole('button',{name:'Sign in',exact:true}).click()
  await expect(page).toHaveURL(/#bookings$/)
  await expect(page.getByText('Sign in to view bookings',{exact:true})).toHaveCount(0)
  await expect(page.getByText('No bookings yet',{exact:true})).toBeVisible()
})

test('route illustration is honest, static for reduced motion, and footer fits mobile',async({page})=>{
  await page.emulateMedia({reducedMotion:'reduce'})
  await page.setViewportSize({width:1440,height:900})
  await page.goto('/')
  await expect(page.getByText('Route illustration · not live tracking',{exact:true})).toBeVisible()
  expect(await page.locator('.illustrated-route').evaluate(element=>getComputedStyle(element).animationName)).toBe('none')
  await page.setViewportSize({width:390,height:844})
  await expect(page.locator('.route-illustration')).toBeHidden()
  await expect(page.getByRole('contentinfo').getByText('Monday–Friday · 10:00–18:00 IST',{exact:true})).toBeVisible()
  expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true)
  await page.screenshot({path:'test-results/ui-followup-mobile.png',fullPage:true})
})
