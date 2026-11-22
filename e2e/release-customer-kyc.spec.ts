import {expect,test} from '@playwright/test'
import {providerAccount} from './fixtures/accounts'
import {signIn} from './fixtures/api'
import {api,fixture,demandPayload,auth,startAndUpload,cleanAndSubmit,approve} from './fixtures/customerJourney'

for(const width of [1440,390])test(`customer consent, scan retry and protected admin review at ${width}px`,async({browser},testInfo)=>{
 test.setTimeout(150000)
 const data=fixture(),customer=await browser.newContext({viewport:{width,height:950}}),admin=await browser.newContext({viewport:{width,height:950}}),other=await browser.newContext()
 try{
  const c=await customer.newPage(),a=await admin.newPage(),o=await other.newPage()
  await signIn(c,data.customer_email,providerAccount.password,'My requirements')
  let recover=false
  await c.route(api+'/customer-kyc/policy',route=>{if(!recover){return route.fulfill({status:503,contentType:'application/json',body:JSON.stringify({detail:'Temporary local policy unavailable'})})}return route.continue()})
  await c.goto('/#kyc')
  await expect(c.getByRole('alert')).toContainText('Temporary local policy unavailable')
  recover=true
  await c.getByRole('button',{name:'Retry customer verification',exact:true}).click()
  await expect(c.getByText('Required documents: PAN.',{exact:true})).toBeVisible()
  await c.screenshot({path:testInfo.outputPath('configured-consent.png'),fullPage:true})
  const {application,storage_key}=await startAndUpload(c)
  await expect(c.getByRole('button',{name:'Submit customer documents for review',exact:true})).toBeDisabled()
  let published=await c.request.post(api+'/demands',{headers:await auth(c),data:demandPayload(data)})
  expect(published.status()).toBe(403)
  expect((await c.request.get(api+'/customer-kyc/admin/applications',{headers:await auth(c)})).status()).toBe(403)
  await c.screenshot({path:testInfo.outputPath('scan-pending-retry.png'),fullPage:true})
  await cleanAndSubmit(c,storage_key)
  published=await c.request.post(api+'/demands',{headers:await auth(c),data:demandPayload(data)})
  expect(published.status()).toBe(403)
  const current=await c.request.get(api+'/customer-kyc/me',{headers:await auth(c)}),doc=(await current.json()).documents[0]
  await signIn(o,data.other_customer_email,providerAccount.password,'My requirements')
  expect((await o.request.get(api+'/customer-kyc/documents/'+doc.id+'/download',{headers:await auth(o)})).status()).toBe(404)
  await signIn(a,data.admin_email,providerAccount.password,'Marketplace control centre')
  await approve(a,application.id)
  const download=await a.request.get(api+'/customer-kyc/documents/'+doc.id+'/download',{headers:await auth(a)})
  expect(download.status()).toBe(200)
  expect((await a.request.get((await download.json()).download_url)).status()).toBe(200)
  await a.screenshot({path:testInfo.outputPath('customer-review-recorded.png'),fullPage:true})
  await c.getByRole('button',{name:'Refresh customer verification',exact:true}).click()
  await expect(c.getByRole('heading',{name:'Application: verified',exact:true})).toBeVisible()
  published=await c.request.post(api+'/demands',{headers:await auth(c),data:demandPayload(data)})
  expect(published.status()).toBe(201)
  expect(await c.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true)
  await c.screenshot({path:testInfo.outputPath('customer-verified-publication.png'),fullPage:true})
 }finally{await customer.close();await admin.close();await other.close()}
})
