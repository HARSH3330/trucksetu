import {expect,test,type Page} from '@playwright/test'
import {spawnSync} from 'node:child_process'
import path from 'node:path'
import {adminAccount,providerAccount} from './fixtures/accounts'
import {accessToken,captureApiFailures,signIn} from './fixtures/api'

const api=(process.env.E2E_API_URL||'http://127.0.0.1:8000/api/v1').replace(/\/$/,'')
async function localTime(page:Page,value:string){
  // Minute-resolution inputs must not round pickup BEFORE a seconds-resolution
  // seeded window. Choose the next valid minute, inside the one-hour window.
  return page.evaluate(value=>{const date=new Date(Math.ceil(new Date(value).getTime()/60000)*60000);return `${date.getFullYear()}-${String(date.getMonth()+1).padStart(2,'0')}-${String(date.getDate()).padStart(2,'0')}T${String(date.getHours()).padStart(2,'0')}:${String(date.getMinutes()).padStart(2,'0')}`},value)
}

for(const prerequisites of ['seeded','ui-created'] as const)test(`real ${prerequisites} route/request, provider quotation, admin suitability, customer acceptance and cancellation`,async({browser})=>{
  const fixture=spawnSync(process.env.E2E_PYTHON||'python',[path.resolve('e2e/fixtures/shared_database.py')],{cwd:process.cwd(),env:process.env,encoding:'utf8',input:JSON.stringify({password:providerAccount.password})})
  expect(fixture.status,'Guarded local shared prerequisites (details redacted)').toBe(0)
  const data=JSON.parse(fixture.stdout)
  const provider=await browser.newContext(),customer=await browser.newContext(),admin=await browser.newContext()
  let failed=false
  try{
    const p=await provider.newPage(),c=await customer.newPage(),a=await admin.newPage()
    for(const page of [p,c,a])captureApiFailures(page)
    await signIn(p,data.provider_email,providerAccount.password)
    if(prerequisites==='ui-created'){
      // Only fictional identities, existing compliance fixtures and category are
      // seeded. The route and shipment actually used below are created in UI.
      await p.setViewportSize({width:390,height:844})
      await p.goto('/#capacity',{waitUntil:'domcontentloaded'})
      await p.getByText('Publish shared capacity',{exact:true}).click()
      const form=p.getByRole('form',{name:'Publish shared capacity',exact:true})
      await form.getByLabel('Route vehicle',{exact:true}).selectOption(data.vehicle_id)
      await form.getByLabel('Route driver',{exact:true}).selectOption(data.driver_id)
      for(const [label,value] of [
        ['Route origin city','Delhi'],['Route destination city','Noida'],
        ['Route origin address','NOT REAL Delhi loading depot'],['Route destination address','NOT REAL Noida unloading depot'],
        ['Departure start',await localTime(p,data.pickup)],
        ['Departure window end',await localTime(p,new Date(new Date(data.pickup).getTime()+3600000).toISOString())],
        ['Expected arrival',await localTime(p,data.delivery)],
        ['Total weight capacity (tonnes)','1.1'],['Available weight (tonnes)','1.1'],
        ['Total volume (m³)','1.1'],['Available volume (m³)','1.1'],['Minimum booking weight (tonnes)','0.1'],
        ['Route price (INR)','123'],['Minimum acceptable earning (INR)','100'],
        ['Maximum deviation (km)','10'],['Maximum added time (minutes)','60'],['Allowed cargo types','Furniture'],
      ])await form.getByLabel(label,{exact:true}).fill(value)
      await form.getByLabel('Price basis',{exact:true}).selectOption('negotiated')
      const published=p.waitForResponse(response=>new URL(response.url()).pathname==='/api/v1/available-routes'&&response.request().method()==='POST')
      await form.getByRole('button',{name:'Publish route',exact:true}).click()
      const routeResponse=await published
      expect(routeResponse.status(),'UI route publication (values redacted)').toBe(201)
      const route=await routeResponse.json()
      data.route_id=route.id
      data.pickup=route.departure_at
      data.delivery=route.expected_arrival_at
      await expect(p.getByText(`Published route ${route.id}`,{exact:true})).toBeVisible()

      await signIn(c,data.customer_email,providerAccount.password)
      await c.setViewportSize({width:390,height:844})
      await c.goto('/#capacity',{waitUntil:'domcontentloaded'})
      await c.getByLabel('Origin',{exact:true}).fill('Delhi')
      await c.getByLabel('Destination',{exact:true}).fill('Noida')
      const searched=c.waitForResponse(response=>new URL(response.url()).pathname==='/api/v1/available-routes'&&response.request().method()==='GET')
      await c.getByRole('button',{name:'Search routes',exact:true}).click()
      const searchResponse=await searched
      expect(searchResponse.status()).toBe(200)
      const results=await searchResponse.json()
      // Scope by this route's unique selected reference instead of accepting
      // whichever pre-existing fixture happens to be first in search results.
      const routeIndex=results.findIndex((item:{id:string})=>item.id===route.id)
      expect(routeIndex,'Newly published route is actually returned by search').toBeGreaterThanOrEqual(0)
      const card=c.locator('.capacity-card').nth(routeIndex)
      await card.getByText('Request capacity on this route',{exact:true}).click()
      for(const [label,value] of [
        ['Cargo category','Furniture'],['Cargo description','NOT A REAL SHIPMENT: local harmless cartons'],
        ['Weight (tonnes)','1'],['Total cargo length (m)','1'],['Total cargo width (m)','1'],['Total cargo height (m)','1'],
        ['Earliest pickup',await localTime(c,data.pickup)],
        ['Latest pickup',await localTime(c,new Date(new Date(data.pickup).getTime()+3600000).toISOString())],
        ['Delivery deadline',await localTime(c,new Date(new Date(data.delivery).getTime()+7200000).toISOString())],
        ['Maximum added time (minutes)','60'],
      ])await card.getByLabel(label,{exact:true}).fill(value)
      const requested=c.waitForResponse(response=>new URL(response.url()).pathname==='/api/v1/requests'&&response.request().method()==='POST')
      await card.getByRole('button',{name:'Request provider quotation',exact:true}).click()
      const requestResponse=await requested
      expect(requestResponse.status(),'UI shipment creation (values redacted)').toBe(201)
      const shipment=await requestResponse.json()
      expect(shipment.available_route_id).toBe(route.id)
      data.request_id=shipment.id
      await expect(card.getByText(/This does not reserve capacity/)).toBeVisible()
      expect(await c.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true)
    }
    await p.goto('/#capacity',{waitUntil:'domcontentloaded'})
    await p.getByText('Quote selected-route capacity requests',{exact:true}).click()
    await p.getByRole('combobox',{name:'Capacity request',exact:true}).selectOption(data.request_id)
    await p.getByRole('combobox',{name:'Route vehicle category',exact:true}).selectOption(data.category_id)
    for(const [label,value] of [
      ['Final payable total (INR)','750'],['Estimated pickup',await localTime(p,data.pickup)],
      ['Estimated delivery',await localTime(p,data.delivery)],['Quote valid until',await localTime(p,new Date(Date.now()+3600000).toISOString())],
      ['Included charges/services','Transport'],['Excluded charges/services (state None if none)','None'],
      ['Charge name','Transport'],['Charge amount (INR)','750'],
    ])await p.getByLabel(label,{exact:true}).fill(value)
    const quoteResponse=p.waitForResponse(response=>new URL(response.url()).pathname===`/api/v1/requests/${data.request_id}/quotes`&&response.request().method()==='POST')
    await p.getByRole('button',{name:'Submit final shared quotation',exact:true}).click()
    expect((await quoteResponse).status()).toBe(201)
    await expect(p.getByText('Shared quotation submitted. No capacity or payment is guaranteed until customer acceptance succeeds.',{exact:true})).toBeVisible()

    await signIn(a,adminAccount.email,adminAccount.password)
    await a.getByText('Shared route suitability review',{exact:true}).click()
    await a.getByRole('combobox',{name:'Shared request to review',exact:true}).selectOption(data.request_id)
    for(const [label,value] of [['Reviewed added distance (km)','0'],['Reviewed added time (minutes)','0'],['Reviewed route fit (%)','100'],['Additional toll/permit cost (INR)','0'],['Handling/waiting allowance (INR)','0'],['Dedicated comparable price (INR)','1000'],['Provider final quote amount (INR)','750']])await a.getByLabel(label,{exact:true}).fill(value)
    for(const label of ['Pickup window reviewed feasible','Delivery deadline reviewed feasible','Existing commitments reviewed feasible'])await a.getByLabel(label,{exact:true}).check()
    await a.getByRole('button',{name:'Record suitability evaluation',exact:true}).click()
    await expect(a.getByText('Eligible. Acceptance still rechecks capacity, documents, timing and price.',{exact:true})).toBeVisible()

    if(prerequisites==='seeded')await signIn(c,data.customer_email,providerAccount.password)
    await c.goto('/#quotes',{waitUntil:'domcontentloaded'})
    const accept=c.getByRole('button',{name:'Accept quote and book shared capacity',exact:true})
    await expect(accept).toBeDisabled()
    const holdResponse=c.waitForResponse(response=>new URL(response.url()).pathname.endsWith('/reservations')&&response.request().method()==='POST')
    await c.getByRole('button',{name:'Hold available capacity temporarily',exact:true}).click()
    expect((await holdResponse).status()).toBe(201)
    await expect(c.getByText(/Temporary hold expires in/)).toBeVisible()
    await c.getByRole('checkbox',{name:'I accept this exact quotation revision and final payable total.'}).check()
    const bookedResponse=c.waitForResponse(response=>new URL(response.url()).pathname.endsWith('/accept-shared')&&response.request().method()==='POST')
    await accept.click()
    const response=await bookedResponse
    expect(response.status()).toBe(201)
    const booked=await response.json()
    expect(booked.total_amount).toBe('750.00');expect(booked.status).toBe('advance_pending')
    await expect(c.getByRole('heading',{name:'Booking created',exact:true})).toBeVisible()
    await expect(c.getByText('Payment remains pending until a configured payment method is used.',{exact:true})).toBeVisible()
    // Cancellation currently has no customer UI control; exercise its actual protected API.
    const headers={Authorization:`Bearer ${await accessToken(c)}`}
    expect((await c.request.post(`${api}/bookings/${booked.id}/cancel`,{headers,data:{reason_code:'fictional-test'}})).status()).toBe(201)
    expect((await c.request.post(`${api}/bookings/${booked.id}/cancel`,{headers,data:{reason_code:'fictional-test'}})).status()).toBe(409)
    const remaining=await c.request.get(`${api}/available-routes?origin=Delhi&destination=Noida`)
    expect(remaining.status()).toBe(200)
    const route=(await remaining.json()).find((item:{id:string})=>item.id===data.route_id)
    expect(route.remaining_capacity_tonnes).toBe('1.100')
    await c.goto('/#bookings',{waitUntil:'domcontentloaded'})
    await expect(c.getByText('CANCELLED',{exact:true})).toBeVisible()
  }catch(error){failed=true;throw error}
  finally{
    const cleanup=await Promise.allSettled([provider,customer,admin].map(context=>context.close()))
    if(cleanup.some(result=>result.status==='rejected')){
      if(failed)console.error('Shared context cleanup failed; original failure preserved')
      else throw new Error('Shared browser context cleanup failed')
    }
  }
})
