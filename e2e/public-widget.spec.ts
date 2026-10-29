import {expect,test,type Page} from '@playwright/test'

async function openVerification(page:Page,result:'accepted'|'denied'|'not-confirmed',startWidget=true){
  let verified=false
  let submissions=0
  const proof='fictional-browser-proof-not-valid-at-MSG91'
  await page.addInitScript(()=>sessionStorage.setItem('transivox_access_token','fictional-browser-session-only'))
  await page.route('**/api/v1/**',async route=>{
    const path=new URL(route.request().url()).pathname
    if(path==='/api/v1/auth/me')return route.fulfill({json:{id:'00000000-0000-4000-8000-000000000001',full_name:'Fictional browser account',roles:['customer'],mobile:'+919999999999',mobile_verified:verified}})
    if(path==='/api/v1/dashboard/summary')return route.fulfill({json:{roles:['customer'],open_requests:0,active_quotes:0,active_bookings:0,active_trips:0,completed_bookings:0,total_booking_value:'0',provider_rating:null,provider_kyc_status:null}})
    if(path==='/api/v1/auth/mobile'){
      verified=true;return route.fulfill({json:{updated:true,mobile_verified:true}})
    }
    if(path==='/api/v1/auth/mobile/verify-widget'){
      submissions++
      expect(route.request().postDataJSON()).toEqual({verification_token:proof})
      if(result==='denied')return route.fulfill({status:400,json:{detail:'Invalid or expired phone verification'}})
      if(result==='not-confirmed')return route.fulfill({json:{mobile_verified:false}})
      verified=true;return route.fulfill({json:{mobile_verified:true}})
    }
    if(path==='/api/v1/requests')return route.fulfill({json:[]})
    return route.fulfill({status:503,json:{detail:'Unconfigured local browser-test boundary'}})
  })
  // Fake ONLY the external widget script and API boundary. This browser test
  // does not prove real login/PostgreSQL/MSG91; backend regressions are separate.
  await page.route('https://verify.msg91.com/otp-provider.js',route=>route.abort())
  await page.route('https://verify.phone91.com/otp-provider.js',route=>route.fulfill({contentType:'application/javascript',body:`window.initSendOTP=function(configuration){const element=document.createElement('msg91-otp-provider');element.style.cssText='position:fixed;top:240px;left:20px;z-index:9999999;background:white;padding:16px';const button=document.createElement('button');button.textContent='Complete fake provider verification';button.onclick=function(){configuration.success({type:'success',message:'${proof}'})};element.append(button);document.body.append(element)}`}))
  // Prevent any unexpected provider network call; never send a real SMS.
  await page.route('https://api.msg91.com/**',route=>route.abort())
  await page.route('https://control.msg91.com/**',route=>route.abort())
  await page.goto('/')
  await expect(page.getByRole('button',{name:'Sign out',exact:true})).toBeVisible()
  if(!await page.getByRole('button',{name:'Account help',exact:true}).isVisible())await page.getByRole('button',{name:'Open navigation',exact:true}).click()
  await page.getByRole('button',{name:'Account help',exact:true}).click()
  await page.getByRole('button',{name:'Trip contact',exact:true}).click()
  await expect(page.getByText('+919999999999 · not verified',{exact:true})).toBeVisible()
  if(!startWidget)return ()=>submissions
  await page.getByRole('button',{name:'Verify saved phone (send OTP)',exact:true}).click()
  await expect(page.getByRole('button',{name:'Complete fake provider verification',exact:true})).toBeVisible()
  return ()=>submissions
}

test('widget success waits for backend validation and denied proof stays unverified',async({page})=>{
  const count=await openVerification(page,'denied')
  await page.getByRole('button',{name:'Complete fake provider verification',exact:true}).click()
  await expect(page.getByText('Invalid or expired phone verification',{exact:true})).toBeVisible()
  await expect(page.getByText('+919999999999 · not verified',{exact:true})).toBeVisible()
  expect(count()).toBe(1)
})

test('accepted server proof refreshes verified state and widget cleans up on close',async({page})=>{
  await page.setViewportSize({width:390,height:844})
  const count=await openVerification(page,'accepted')
  await page.getByRole('button',{name:'Complete fake provider verification',exact:true}).click()
  await expect(page.getByText('+919999999999 · verified',{exact:true})).toBeVisible()
  expect(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth)).toBe(false)
  expect(count()).toBe(1)
  await page.getByRole('button',{name:'Close account help',exact:true}).click()
  await expect(page.locator('msg91-otp-provider')).toHaveCount(0)
})

test('cancelled widget callback cannot submit verification proof',async({page})=>{
  const count=await openVerification(page,'accepted')
  await page.evaluate(()=>{(window as unknown as {lateWidgetButton:HTMLElement}).lateWidgetButton=document.querySelector('msg91-otp-provider button') as HTMLElement})
  await page.getByRole('button',{name:'Cancel phone verification',exact:true}).click()
  await page.evaluate(()=>(window as unknown as {lateWidgetButton:HTMLElement}).lateWidgetButton.click())
  expect(count()).toBe(0)
  await expect(page.getByText('+919999999999 · not verified',{exact:true})).toBeVisible()
})

test('HTTP success without explicit verification confirmation stays unverified',async({page})=>{
  await openVerification(page,'not-confirmed')
  await page.getByRole('button',{name:'Complete fake provider verification',exact:true}).click()
  await expect(page.getByText('The server did not confirm phone verification.',{exact:true})).toBeVisible()
  await expect(page.getByText('+919999999999 · not verified',{exact:true})).toBeVisible()
})

test('saving an unchanged verified phone does not show false unverified copy',async({page})=>{
  await openVerification(page,'accepted',false)
  await page.getByLabel('Mobile for trip OTP',{exact:true}).fill('+919999999999')
  await page.getByLabel('Current password',{exact:true}).fill('FictionalOnly123!')
  await page.getByRole('button',{name:'Save trip contact',exact:true}).click()
  await expect(page.getByText('Trip contact saved. Existing phone verification retained.',{exact:true})).toBeVisible()
  await expect(page.getByText('+919999999999 · verified',{exact:true})).toBeVisible()
})
