import {expect,test} from '@playwright/test'

test('admin records explicit shared suitability evidence and runs hold expiry',async({page})=>{
  await page.addInitScript(()=>sessionStorage.setItem('transivox_access_token','fictional-access'))
  let evaluated=false,released=false
  await page.route('**/api/v1/**',route=>{
    const path=new URL(route.request().url()).pathname
    if(path.endsWith('/auth/me'))return route.fulfill({json:{id:'fictional-admin',full_name:'Fictional admin',roles:['admin']}})
    if(path.endsWith('/marketplace-health'))return route.fulfill({json:{verified_providers:0,approved_vehicles:0,open_requests:1,active_quotes:0,active_bookings:0,open_disputes:0,pending_kyc:0,gmv:'0',total_bookings:0,completed_bookings:0,completion_rate:0}})
    if(path.endsWith('/analytics/funnel'))return route.fulfill({json:{period_days:30,funnel:[]}})
    if(path.endsWith('/admin/users'))return route.fulfill({json:{items:[],total:0,page:1,page_size:25}})
    if(path.endsWith('/requests'))return route.fulfill({json:[{id:'fictional-request',public_id:'TEST-REVIEW',available_route_id:'fictional-route',booking_mode:'SHARED_CAPACITY'}]})
    if(path.endsWith('/evaluate-shared-match')){const payload=route.request().postDataJSON();expect(payload.proposed_shared_price).toBe('750');expect(payload.pickup_window_feasible).toBe(true);evaluated=true;return route.fulfill({status:201,json:{eligible:true,rejection_reasons:[],explanation:['Fictional review'],expires_at:'2099-01-01T00:00:00Z'}})}
    if(path.endsWith('/capacity/release-expired')){released=true;return route.fulfill({json:{released:0}})}
    return route.fulfill({status:404,json:{detail:'Unknown synthetic boundary'}})
  })
  await page.goto('/#admin')
  await page.getByText('Shared route suitability review',{exact:true}).click()
  await page.setViewportSize({width:390,height:844})
  expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true)
  await page.getByLabel('Shared request to review').selectOption('fictional-request')
  for(const [label,value] of [['Reviewed added distance (km)','0'],['Reviewed added time (minutes)','0'],['Reviewed route fit (%)','100'],['Additional toll/permit cost (INR)','0'],['Handling/waiting allowance (INR)','0'],['Dedicated comparable price (INR)','1000'],['Provider final quote amount (INR)','750']])await page.getByLabel(label,{exact:true}).fill(value)
  for(const label of ['Pickup window reviewed feasible','Delivery deadline reviewed feasible','Existing commitments reviewed feasible'])await page.getByLabel(label,{exact:true}).check()
  await page.getByRole('button',{name:'Record suitability evaluation',exact:true}).click()
  await expect(page.getByText('Eligible. Acceptance still rechecks capacity, documents, timing and price.',{exact:true})).toBeVisible()
  await page.getByRole('button',{name:'Release expired unbooked holds',exact:true}).click()
  await expect(page.getByText('Expired holds released: 0',{exact:true})).toBeVisible()
  expect(evaluated&&released).toBe(true)
})

test('provider publishes a fresh complete shared quotation revision',async({page})=>{
  await page.addInitScript(()=>sessionStorage.setItem('transivox_access_token','fictional-access'))
  let revised=false
  await page.route('**/api/v1/**',route=>{
    const path=new URL(route.request().url()).pathname
    if(path.endsWith('/auth/me'))return route.fulfill({json:{id:'fictional-provider-user',full_name:'Fictional provider',roles:['provider']}})
    if(path.endsWith('/providers/me'))return route.fulfill({json:{id:'fictional-provider',provider_type:'owner',kyc_status:'verified',active:true}})
    if(path.endsWith('/quotes/mine'))return route.fulfill({json:[{id:'fictional-quote',request_id:'fictional-request',service_mode:'SHARED_CAPACITY',version:2,status:'active',final_price:'750',price_breakdown:[{label:'Transport',amount:'750'}],inclusions:'Transport',exclusions:'None',expires_at:'2099-01-01T00:00:00Z'}]})
    if(path.endsWith('/quotes/fictional-quote')&&route.request().method()==='PATCH'){
      const body=route.request().postDataJSON();expect(body.final_price).toBe('800');expect(body.price_breakdown).toEqual([{label:'Transport',amount:'800'}]);revised=true
      return route.fulfill({json:{id:'fictional-quote',version:3}})
    }
    if(path.endsWith('/available-routes')||path.endsWith('/requests')||path.endsWith('/vehicle-categories')||path.endsWith('/carrier-vehicles')||path.endsWith('/drivers'))return route.fulfill({json:[]})
    return route.fulfill({status:404,json:{detail:'Unknown synthetic boundary'}})
  })
  await page.goto('/#capacity')
  await page.getByText('Revise my shared quotations',{exact:true}).click()
  await page.setViewportSize({width:390,height:844})
  expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true)
  await page.getByLabel('Revised final total (INR)').fill('800')
  await page.getByLabel('Revised charge amount 1').fill('800')
  await page.getByRole('button',{name:'Publish new quotation revision',exact:true}).click()
  await expect(page.getByText('Revision 3 published. Customer must explicitly accept the new revision.',{exact:true})).toBeVisible()
  expect(revised).toBe(true)
})

test('customer explicitly accepts the displayed shared quote revision without submitting a payable total',async({page})=>{
  await page.addInitScript(()=>sessionStorage.setItem('transivox_access_token','fictional-access'))
  let submitted:Record<string,unknown>|undefined
  await page.route('**/api/v1/**',route=>{
    const path=new URL(route.request().url()).pathname
    if(path.endsWith('/auth/me'))return route.fulfill({json:{id:'fictional-customer',full_name:'Fictional customer',roles:['customer']}})
    if(path.endsWith('/requests/mine'))return route.fulfill({json:[{id:'fictional-request',public_id:'TEST-SHARED',status:'published',vehicle_count:1,booking_mode:'SHARED_CAPACITY',pickup_address:'Test pickup',destination_address:'Test drop'}]})
    if(path.endsWith('/quotes'))return route.fulfill({json:[{id:'fictional-quote',request_id:'fictional-request',available_route_id:'fictional-route',service_mode:'SHARED_CAPACITY',provider_name:'Fictional provider',verified:true,rating:'0',completed_trips:0,cancellation_percent:'0',vehicle_name:'Test truck',final_price:'750.00',vehicles_offered:1,status:'active',version:2,expires_at:'2099-01-01T00:00:00Z',price_breakdown:[{label:'Transport',amount:'500.00'},{label:'Declared handling',amount:'250.00'}],currency:'INR',inclusions:'Declared handling',exclusions:'None'}]})
    if(path.endsWith('/legal/terms/acceptance'))return route.fulfill({json:{accepted:true}})
    if(path.endsWith('/accept-shared')){submitted=route.request().postDataJSON();return route.fulfill({status:201,json:{id:'fictional-booking',public_id:'TEST-BOOKED-SHARED',trucks_allocated:1,total_amount:'750.00',request_allocation:'1 / 1'}})}
    return route.fulfill({status:404,json:{detail:'Unknown test boundary'}})
  })
  await page.goto('/#quotes',{waitUntil:'domcontentloaded'})
  const accept=page.getByRole('button',{name:'Accept quote and book shared capacity',exact:true})
  await expect(accept).toBeDisabled()
  await page.getByRole('checkbox',{name:'I accept this exact quotation revision and final payable total.'}).check()
  await accept.click()
  await expect(page.getByText('TEST-BOOKED-SHARED',{exact:true})).toBeVisible()
  expect(submitted?.expected_version).toBe(2)
  expect(submitted?.accept_final_price).toBe(true)
  expect(submitted?.idempotency_key).toBeTruthy()
  expect(submitted).not.toHaveProperty('total_amount')
  await expect(page.getByText('Payment remains pending until a configured payment method is used.')).toBeVisible()
})
