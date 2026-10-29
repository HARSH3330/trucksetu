import {expect,test,type Page} from '@playwright/test'
import {spawnSync} from 'node:child_process'
import path from 'node:path'
import {randomUUID} from 'node:crypto'
import {adminAccount,providerAccount} from './fixtures/accounts'
import {accessToken,captureApiFailures,signIn} from './fixtures/api'
import {createIdentityTestPdf} from './fixtures/pdf'

const api=(process.env.E2E_API_URL||'http://127.0.0.1:8000/api/v1').replace(/\/$/,'')
const control=process.env.E2E_CONTROL_TOKEN||'transivox-e2e-control-token'
const kinds=['rc','insurance','fitness','pollution','permit'] as const

test('mobile vehicle creation, protected uploads, scan gate, rejection/replacement and manual approval',async({browser},testInfo)=>{
  // Six upload/scan cycles and independent manual reviews run sequentially.
  test.setTimeout(120_000)
  const fixture=spawnSync(process.env.E2E_PYTHON||'python',[path.resolve('e2e/fixtures/shared_database.py')],{cwd:process.cwd(),env:process.env,encoding:'utf8',input:JSON.stringify({password:providerAccount.password})})
  expect(fixture.status,'Guarded fictional identities/category fixture; details redacted').toBe(0)
  const data=JSON.parse(fixture.stdout)
  const provider=await browser.newContext({viewport:{width:390,height:844}}),admin=await browser.newContext({viewport:{width:390,height:844}})
  let originalFailure=false
  try{
    const p=await provider.newPage(),a=await admin.newPage()
    for(const page of [p,a])captureApiFailures(page)
    await signIn(p,data.provider_email,providerAccount.password)
    await p.getByRole('button',{name:'Manage fleet & drivers',exact:true}).click()
    await p.getByRole('button',{name:'Add vehicle',exact:true}).click()
    const registration='TEST-'+randomUUID().slice(0,8).toUpperCase()
    const expiry=new Date(Date.now()+7*86400000).toISOString().slice(0,10)
    await p.getByRole('combobox',{name:'Vehicle category',exact:true}).selectOption(data.category_id)
    for(const [label,value] of [
      ['Registration number',registration],['Maximum payload (tonnes)','2'],
      ['Internal length (m)','2'],['Internal width (m)','2'],['Internal height (m)','2'],
      ['Permit territories','Delhi, Noida'],['Service areas','Delhi, Noida'],
      ['RC expiry',expiry],['Insurance expiry',expiry],['Fitness expiry',expiry],
      ['Pollution certificate expiry',expiry],['Permit expiry',expiry],
    ])await p.getByLabel(label,{exact:true}).fill(value)
    const created=p.waitForResponse(response=>new URL(response.url()).pathname==='/api/v1/carrier-vehicles'&&response.request().method()==='POST')
    await p.getByRole('button',{name:'Submit vehicle',exact:true}).click()
    const response=await created
    expect(response.status()).toBe(201)
    const vehicle=await response.json()
    const fleetCard=p.locator('.fleet-list article').filter({has:p.getByText(registration,{exact:true})})
    await fleetCard.getByText('Private documents',{exact:true}).click()
    async function upload(kind:string,name=`${kind}-fictional.pdf`){
      await fleetCard.getByRole('combobox',{name:'Document type',exact:true}).selectOption(kind)
      await fleetCard.getByLabel('Document expiry',{exact:true}).fill(expiry)
      await fleetCard.getByLabel('Harmless test or genuine authorised vehicle file',{exact:true}).setInputFiles({name,mimeType:'application/pdf',buffer:createIdentityTestPdf(kind,testInfo.testId)})
      const pending=p.waitForResponse(value=>new URL(value.url()).pathname===`/api/v1/carrier-vehicles/${vehicle.id}/documents`&&value.request().method()==='POST')
      await fleetCard.getByRole('button',{name:'Upload private document',exact:true}).click()
      const blocked=await pending
      expect(blocked.status(),'Missing scan must prevent registration').toBe(409)
      const key=blocked.request().postDataJSON().storage_key
      expect((await p.request.post(`${new URL(api).origin}/__e2e__/scan/clean`,{headers:{'X-E2E-Control-Token':control},data:{storage_key:key}})).status()).toBe(200)
      const registered=p.waitForResponse(value=>new URL(value.url()).pathname===`/api/v1/carrier-vehicles/${vehicle.id}/documents`&&value.request().method()==='POST')
      await fleetCard.getByRole('button',{name:'Check scan again',exact:true}).click()
      expect((await registered).status()).toBe(201)
      await expect(fleetCard.getByText(`${kind}: ${name}`,{exact:true})).toBeVisible()
    }
    await upload('rc')
    await signIn(a,adminAccount.email,adminAccount.password)
    const headers={Authorization:`Bearer ${await accessToken(a)}`}
    const premature=await a.request.post(`${api}/admin/carrier-vehicles/${vehicle.id}/review`,{headers,data:{status:'approved',reason:'Harmless prerequisite test'}})
    expect(premature.status()).toBe(422)
    for(const kind of kinds.slice(1))await upload(kind)
    async function reviewCard(page:Page){
      await page.goto('/#vehicle-review',{waitUntil:'domcontentloaded'})
      // Refresh documents changed by the independent provider browser.
      await page.reload({waitUntil:'domcontentloaded'})
      const card=page.locator('.vehicle-review-list article').filter({has:page.getByText(registration,{exact:true})})
      await card.getByText('Private document review',{exact:true}).click()
      await card.getByRole('textbox',{name:'Document review reason',exact:true}).fill('Harmless fictional file manually reviewed')
      return card
    }
    let card=await reviewCard(a)
    const first=card.locator('.document-list article').filter({hasText:'rc-fictional.pdf'})
    const docList=await a.request.get(`${api}/carrier-vehicles/${vehicle.id}/documents`,{headers})
    const docs=await docList.json()
    const rc=docs.find((item:{type:string})=>item.type==='rc')
    expect((await browser.newContext().then(async context=>{try{return await context.request.get(`${api}/carrier-vehicles/${vehicle.id}/documents/${rc.id}/download`)}finally{await context.close()}})).status()).toBe(401)
    const protectedFile=await a.request.get(`${api}/carrier-vehicles/${vehicle.id}/documents/${rc.id}/download`,{headers})
    expect(protectedFile.status()).toBe(200)
    const file=await a.request.get((await protectedFile.json()).download_url)
    expect(await file.body()).toEqual(createIdentityTestPdf('rc',testInfo.testId))
    await first.getByRole('button',{name:'Reject document',exact:true}).click()
    await expect(first.getByText(/rejected/)).toBeVisible()
    await p.reload()
    await fleetCard.getByText('Private documents',{exact:true}).click()
    await expect(fleetCard.getByText('Harmless fictional file manually reviewed',{exact:true})).toBeVisible()
    await upload('rc','rc-corrected-fictional.pdf')
    card=await reviewCard(a)
    for(const kind of kinds){
      const name=kind==='rc'?'rc-corrected-fictional.pdf':`${kind}-fictional.pdf`
      await card.locator('.document-list article').filter({hasText:name}).getByRole('button',{name:'Accept document',exact:true}).click()
    }
    await card.getByRole('button',{name:'Approve',exact:true}).click()
    const decision=a.locator('.vehicle-decision')
    await decision.getByRole('textbox',{name:'Review reason',exact:true}).fill('All five harmless current files manually accepted')
    await decision.getByRole('button',{name:'Confirm approved',exact:true}).click()
    await a.getByRole('button',{name:/^approved /}).click()
    await expect(a.getByText(registration,{exact:true})).toBeVisible()
    await p.reload()
    await expect(fleetCard.getByText('approved · documents current',{exact:true})).toBeVisible()
    expect(await p.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true)
  }catch(error){originalFailure=true;throw error}
  finally{
    const results=await Promise.allSettled([provider.close(),admin.close()])
    if(results.some(result=>result.status==='rejected')){
      if(originalFailure)console.error('Vehicle context cleanup failed; original failure preserved')
      else throw new Error('Vehicle browser context cleanup failed')
    }
  }
})
