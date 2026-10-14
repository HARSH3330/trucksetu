import {expect,test} from '@playwright/test'

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
  await page.route('**/auth/login',route=>route.fulfill({json:{access_token:'fictional-ux-session',refresh_token:'fictional-ux-refresh',user:{id:'00000000-0000-4000-8000-000000000004',full_name:'Fictional customer',email:'ux.customer@example.com',roles:['customer']}}}))
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
    if(path.endsWith('/auth/login'))return route.fulfill({json:{access_token:'fictional-ux-session',refresh_token:'fictional-ux-refresh',user:{id:'00000000-0000-4000-8000-000000000004',full_name:'Fictional customer',email:'ux.customer@example.com',roles:['customer']}}})
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
  await page.setViewportSize({width:390,height:844})
  await page.goto('/')
  await expect(page.getByText('Route illustration · not live tracking',{exact:true})).toBeVisible()
  expect(await page.locator('.illustrated-route').evaluate(element=>getComputedStyle(element).animationName)).toBe('none')
  await expect(page.getByRole('contentinfo').getByText('Monday–Friday · 10:00–18:00 IST',{exact:true})).toBeVisible()
  expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true)
  await page.screenshot({path:'test-results/ui-followup-mobile.png',fullPage:true})
})
