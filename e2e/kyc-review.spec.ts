import {expect, test, type Browser, type BrowserContext, type Page, type TestInfo, type APIResponse} from '@playwright/test'
import {spawnSync} from 'node:child_process'
import path from 'node:path'
import {randomUUID} from 'node:crypto'
import {adminAccount, providerAccount} from './fixtures/accounts'
import {accessToken, captureApiFailures, signIn, reloadProviderDashboard} from './fixtures/api'
import {createIdentityTestPdf} from './fixtures/pdf'

const base=(process.env.E2E_API_URL||'http://127.0.0.1:8000/api/v1').replace(/\/$/,'')
const origin=new URL(base).origin
const control=process.env.E2E_CONTROL_TOKEN||'transivox-e2e-control-token'
type Document={id:string;type:string;status:string}
type Application={id:string;status:string;decision_reason:string|null;documents:Document[]}
type Actor={page:Page;context:BrowserContext;headers:{Authorization:string}}

function inspect(argument:string){
  const result=spawnSync(process.env.E2E_PYTHON||'python',['-m','e2e_inspect',argument],{
    cwd:path.resolve('backend'),encoding:'utf8',env:{...process.env,APP_ENV:'test',TRANSIVOX_E2E:'true',E2E_REAL_AWS:'false'},
  })
  if(result.status!==0)throw new Error('Dedicated local database inspection failed (connection details redacted)')
  return JSON.parse(result.stdout)
}
// Owner rules do not change within one run; avoid repeatedly importing the
// entire Python API stack inside the browser test's deadline.
let ownerRequired:string[]|undefined
const required=()=>ownerRequired??=(inspect('owner-required') as string[])
async function status(response:Pick<APIResponse,'status'|'url'>,wanted:number){
  // Never print raw responses: they can include credentials or signed URLs.
  expect(response.status(),`${new URL(response.url()).pathname.replace(/[0-9a-f-]{36}/g,':id')} HTTP status (response values redacted)`).toBe(wanted)
}
async function denied(response:APIResponse,wanted:number){
  await status(response,wanted)
  const body=await response.json()
  expect(Object.keys(body)).toEqual(['detail'])
  expect(JSON.stringify(body).includes('download_url')).toBe(false)
  expect(JSON.stringify(body).includes('NOT A REAL IDENTITY DOCUMENT')).toBe(false)
}
async function current(actor:Actor):Promise<Application>{
  const response=await actor.context.request.get(`${base}/kyc/applications/me`,{headers:actor.headers});await status(response,200);return response.json()
}
async function review(admin:Actor,id:string,decision:string,document_decisions:Record<string,string>,reason='Harmless automated manual review'){
  return admin.context.request.post(`${base}/kyc/admin/applications/${id}/review`,{headers:admin.headers,data:{decision,document_decisions,reason}})
}
async function upload(actor:Actor,kind:string,run:string){
  const bytes=createIdentityTestPdf(kind,run)
  const prepared=await actor.context.request.post(`${base}/kyc/uploads`,{headers:actor.headers,data:{document_type:kind,filename:`${kind}-fictional.pdf`,content_type:'application/pdf'}})
  await status(prepared,200)
  const {upload_url,storage_key}=await prepared.json()
  await status(await actor.context.request.put(upload_url,{headers:{'Content-Type':'application/pdf'},data:bytes}),200)
  const payload={document_type:kind,storage_key,original_filename:`${kind}-fictional.pdf`,content_type:'application/pdf'}
  await status(await actor.context.request.post(`${base}/kyc/documents`,{headers:actor.headers,data:payload}),409)
  await status(await actor.context.request.post(`${origin}/__e2e__/scan/clean`,{headers:{'X-E2E-Control-Token':control},data:{storage_key}}),200)
  const registered=await actor.context.request.post(`${base}/kyc/documents`,{headers:actor.headers,data:payload});await status(registered,201)
  return {id:(await registered.json()).id as string,bytes,payload}
}
async function application(actor:Actor,run:string,submit=true){
  await actor.page.getByRole('button',{name:'Verification status'}).click()
  await actor.page.getByLabel('Legal name').fill('Fictional review scenario')
  await actor.page.getByLabel('Verification type').selectOption('owner')
  const response=actor.page.waitForResponse(r=>new URL(r.url()).pathname.endsWith('/kyc/applications')&&r.request().method()==='POST')
  await actor.page.getByRole('button',{name:/Create application/}).click()
  const created=await response
  await status(created,201)
  await created.finished()
  await expect(actor.page.getByRole('heading',{name:'Your KYC application',exact:true})).toBeVisible()
  const files:Record<string,Awaited<ReturnType<typeof upload>>>={}
  for(const kind of required())files[kind]=await upload(actor,kind,run)
  const item=await current(actor)
  if(submit)await status(await actor.context.request.post(`${base}/kyc/applications/${item.id}/submit`,{headers:actor.headers}),200)
  return {item:await current(actor),files}
}
async function withActors(browser:Browser,info:TestInfo,scenario:(a:Actor,b:Actor,admin:Actor)=>Promise<void>){
  const contexts:BrowserContext[]=[]
  let failed=false
  try{
    async function actor(role:'provider-a'|'provider-b'|'admin'):Promise<Actor>{
      const context=await browser.newContext({recordVideo:{dir:info.outputPath(`${role}-video`)}});contexts.push(context)
      const page=await context.newPage();captureApiFailures(page)
      const email=role==='admin'?adminAccount.email:`${role}-${randomUUID()}@example.com`
      const password=role==='admin'?adminAccount.password:providerAccount.password
      if(role!=='admin')await status(await context.request.post(`${base}/auth/signup`,{data:{full_name:`Fictional ${role}`,email,password,role:'provider'}}),201)
      await test.step(`Sign in ${role}`,()=>signIn(page,email,password))
      return {context,page,headers:{Authorization:`Bearer ${await accessToken(page)}`}}
    }
    // Independent sessions can authenticate concurrently without sharing state.
    const [a,b,admin]=await Promise.all([actor('provider-a'),actor('provider-b'),actor('admin')])
    await scenario(a,b,admin)
  }catch(error){failed=true;throw error}
  finally{
    if(failed)for(const [index,context] of contexts.entries())for(const page of context.pages()){
      try{await page.screenshot({path:info.outputPath(`review-failure-${index}.png`)})}
      catch{console.error('Screenshot unavailable; original failure preserved')}
    }
    const results=await Promise.allSettled(contexts.map(context=>context.close()))
    if(results.some(result=>result.status==='rejected')){
      if(failed)console.error('Context cleanup failed; original failure preserved')
      else throw new Error('Browser context cleanup failed')
    }
  }
}

test('protected access, approval prerequisites and persisted verification',async({browser},info)=>{
  await withActors(browser,info,async(a,b,admin)=>{
    const {item,files}=await application(a,info.testId)
    const ownB=await application(b,`${info.testId}-provider-b`,false)
    const kinds=required(),decisions=Object.fromEntries(kinds.map(kind=>[kind,'accepted']))
    const original=inspect(item.id)
    expect(original.application.status).toBe('under_review')
    expect(original.documents.every((doc:{status:string})=>doc.status==='uploaded')).toBe(true)
    const document=files[kinds[0]]
    await denied(await b.context.request.get(`${base}/kyc/documents/${document.id}/download`),401)
    const signed=await admin.context.request.get(`${base}/kyc/documents/${document.id}/download`,{headers:admin.headers});await status(signed,200)
    const link=await signed.json();expect(link.expires_in).toBe(300)
    const opened=await admin.context.request.get(link.download_url);await status(opened,200)
    expect((await opened.body()).equals(document.bytes)).toBe(true)
    const signedUrl=new URL(link.download_url)
    await status(await b.context.request.get(`${signedUrl.origin}${signedUrl.pathname}`),403)
    // A signed URL is a temporary bearer capability, issued only after API authorization.
    for(const subset of [{},Object.fromEntries(kinds.slice(0,-1).map(kind=>[kind,'accepted']))]){
      await status(await review(admin,item.id,'verified',subset),422)
      expect(inspect(item.id)).toEqual(original)
    }
    const foreignBefore=inspect(item.id)
    const bBefore=inspect(ownB.item.id)
    await denied(await b.context.request.get(`${base}/kyc/applications/${item.id}`,{headers:b.headers}),404) // no public by-ID route exists
    expect((await current(b)).id).toBe(ownB.item.id)
    await denied(await b.context.request.get(`${base}/kyc/documents/${document.id}/download`,{headers:b.headers}),403)
    await denied(await b.context.request.post(`${base}/kyc/applications/${item.id}/submit`,{headers:b.headers}),409)
    await denied(await b.context.request.post(`${base}/kyc/documents`,{headers:b.headers,data:document.payload}),422)
    await denied(await b.context.request.get(`${base}/kyc/admin/applications`,{headers:b.headers}),403)
    for(const decision of ['verified','rejected','resubmit_required'])await denied(await review(b,item.id,decision,decisions),403)
    expect(inspect(item.id)).toEqual(foreignBefore)
    expect(inspect(ownB.item.id)).toEqual(bBefore)
    await reloadProviderDashboard(b.page);await b.page.getByRole('button',{name:'Verification status'}).click()
    await expect(b.page.getByRole('heading',{name:'Your KYC application'})).toBeVisible()
    await expect(b.page.getByRole('heading',{name:'Verification review queue'})).toHaveCount(0)
    await status(await review(admin,item.id,'verified',decisions),200)
    const approved=inspect(item.id)
    expect(approved.application).toMatchObject({status:'verified',kyc_status:'verified',active:true})
    expect(approved.documents.every((doc:{status:string})=>doc.status==='accepted')).toBe(true)
    expect(approved.reviews).toEqual(expect.arrayContaining([expect.objectContaining({new_status:'verified'})]))
    await reloadProviderDashboard(a.page)
    await expect(a.page.getByText('KYC verified',{exact:true})).toBeVisible()
    await a.page.getByRole('button',{name:'Verification status'}).click()
    await expect(a.page.getByText('verified',{exact:true})).toBeVisible()
    expect((await current(a)).status).toBe('verified')
  })
})

test('document rejection, replacement and resubmission preserve history; terminal rejection stays terminal',async({browser},info)=>{
  await withActors(browser,info,async(a,b,admin)=>{
    const {item}=await application(a,info.testId)
    const kinds=required(),replace=kinds[0]
    const reason='Harmless test reason: fictional document needs replacement'
    await status(await review(admin,item.id,'resubmit_required',{[replace]:'rejected'},reason),200)
    await reloadProviderDashboard(a.page);await a.page.getByRole('button',{name:'Verification status'}).click()
    await expect(a.page.getByText(reason,{exact:true})).toBeVisible()
    await status(await a.context.request.post(`${base}/kyc/applications/${item.id}/submit`,{headers:a.headers}),422)
    const replacement=await upload(a,replace,`${info.testId}-replacement`)
    await status(await a.context.request.post(`${base}/kyc/applications/${item.id}/submit`,{headers:a.headers}),200)
    const resubmitted=inspect(item.id)
    expect(resubmitted.application).toMatchObject({status:'under_review',kyc_status:'under_review'})
    expect(resubmitted.reviews).toEqual(expect.arrayContaining([expect.objectContaining({new_status:'resubmit_required',reason})]))
    await status(await review(admin,item.id,'verified',{}),422)
    expect(inspect(item.id)).toEqual(resubmitted)
    await status(await review(admin,item.id,'verified',Object.fromEntries(kinds.map(kind=>[kind,'accepted']))),200)
    const approved=inspect(item.id)
    expect(approved.documents.find((doc:{id:string})=>doc.id===replacement.id).status).toBe('accepted')
    expect(approved.documents.filter((doc:{document_type:string;id:string})=>doc.document_type===replace&&doc.id!==replacement.id).every((doc:{status:string})=>doc.status==='rejected')).toBe(true)
    // Independent provider B application exercises the terminal rejection rule.
    const rejected=await application(b,`${info.testId}-terminal`)
    const terminalReason='Harmless test terminal rejection reason'
    await status(await review(admin,rejected.item.id,'rejected',{},terminalReason),200)
    await reloadProviderDashboard(b.page);await b.page.getByRole('button',{name:'Verification status'}).click()
    await expect(b.page.getByText(terminalReason,{exact:true})).toBeVisible()
    const terminal=inspect(rejected.item.id)
    await status(await b.context.request.post(`${base}/kyc/applications/${rejected.item.id}/submit`,{headers:b.headers}),409)
    expect(inspect(rejected.item.id)).toEqual(terminal)
    expect(terminal.reviews).toEqual(expect.arrayContaining([expect.objectContaining({new_status:'rejected',reason:terminalReason})]))
  })
})
