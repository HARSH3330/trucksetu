import {expect,type Page} from '@playwright/test'
import {spawnSync} from 'node:child_process'
import path from 'node:path'
import {providerAccount} from './accounts'
import {accessToken} from './api'
export const api=process.env.E2E_API_URL||'http://127.0.0.1:18000/api/v1'
export const origin=new URL(api).origin
export type Fixture={customer_email:string;other_customer_email:string;provider_email:string;admin_email:string;vehicle_id:string;driver_id:string;pickup:string;delivery:string}
export function fixture():Fixture{
 const result=spawnSync(process.env.E2E_PYTHON||'python',[path.resolve('e2e/fixtures/demand_database.py')],{cwd:process.cwd(),env:process.env,input:JSON.stringify({password:providerAccount.password}),encoding:'utf8'})
 expect(result.status,'Guarded synthetic fixture only; output withheld').toBe(0)
 return JSON.parse(result.stdout)
}
export function demandPayload(data:Fixture,description='Fictional furniture for local browser verification'){
 return {reviewed:true,pickup_address:'PRIVATE fictional pickup lane',pickup_city:'Delhi',destination_address:'PRIVATE fictional delivery lane',destination_city:'Noida',booking_mode:'FULL_VEHICLE',schedule_mode:'SCHEDULED',pickup_date:new Intl.DateTimeFormat('en-CA',{timeZone:'Asia/Kolkata'}).format(new Date(data.pickup)),earliest_pickup_at:data.pickup,latest_pickup_at:new Date(new Date(data.pickup).getTime()+3600000).toISOString(),delivery_deadline_at:new Date(new Date(data.delivery).getTime()+3600000).toISOString(),cargo:{category:'Furniture',description,weight_tonnes:'1',length_m:'1',width_m:'1',height_m:'1',packages:1,packaging_type:'Cartons'}}
}
export async function auth(page:Page){return {Authorization:'Bearer '+await accessToken(page)}}
export async function startAndUpload(page:Page){
 await page.goto('/#kyc')
 await expect(page.getByText('FICTIONAL LOCAL CONSENT:',{exact:false})).toBeVisible()
 const button=page.getByRole('button',{name:'Start customer verification',exact:true})
 await expect(button).toBeDisabled()
 const consent=page.getByRole('checkbox',{name:'I have read this customer document consent',exact:false})
 await consent.focus();await page.keyboard.press('Space');await expect(consent).toBeChecked()
 const started=page.waitForResponse(r=>new URL(r.url()).pathname==='/api/v1/customer-kyc/applications'&&r.request().method()==='POST')
 await button.click();const response=await started;expect(response.status()).toBe(201)
 const application=await response.json()
 const prepared=page.waitForResponse(r=>new URL(r.url()).pathname==='/api/v1/customer-kyc/uploads'&&r.request().method()==='POST')
 await page.getByLabel('Upload PAN',{exact:true}).setInputFiles({name:'FICTIONAL-local-sample.pdf',mimeType:'application/pdf',buffer:Buffer.from('%PDF-1.4 FICTIONAL LOCAL SAMPLE ONLY')})
 const upload=await prepared;expect(upload.status()).toBe(200);const {storage_key}=await upload.json()
 await expect(page.getByRole('button',{name:'Check scan and register document',exact:true})).toBeEnabled()
 return {application,storage_key}
}
export async function cleanAndSubmit(page:Page,key:string){
 expect(new URL(origin).hostname).toBe('127.0.0.1')
 const clean=await page.request.post(origin+'/__e2e__/scan/clean',{headers:{'X-E2E-Control-Token':process.env.E2E_CONTROL_TOKEN||'local-regression-control-only'},data:{storage_key:key}})
 expect(clean.status()).toBe(200)
 await page.getByRole('button',{name:'Check scan and register document',exact:true}).click()
 await expect(page.getByText('Scan verified. Document registered for manual review.',{exact:true})).toBeVisible()
 await page.getByRole('button',{name:'Submit customer documents for review',exact:true}).click()
 await expect(page.getByRole('heading',{name:'Application: under review',exact:true})).toBeVisible()
}
export async function approve(page:Page,id:string){
 await page.goto('/#kyc')
 const section=page.getByRole('heading',{name:'Customer document review',exact:true}).locator('..')
 await section.getByRole('button',{name:'Application '+id.slice(0,8),exact:false}).click()
 await section.getByLabel('Customer review reason',{exact:true}).fill('Fictional local manual review of the configured sample document.')
 const record=section.getByRole('button',{name:'Record customer review',exact:true})
 await expect(record).toBeDisabled()
 await section.getByLabel('Decision for PAN',{exact:true}).selectOption('accepted')
 await record.click();await expect(section.getByText('Customer review recorded.',{exact:true})).toBeVisible()
}
