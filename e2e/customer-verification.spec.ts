import {expect,test} from '@playwright/test'
import {spawnSync} from 'node:child_process'
import path from 'node:path'
import {providerAccount} from './fixtures/accounts'
import {signIn} from './fixtures/api'

for(const width of [1440,390])test(`customer verification fails closed without approved document policy at ${width}px`,async({browser},testInfo)=>{
 test.setTimeout(90_000)
 const fixture=spawnSync(process.env.E2E_PYTHON||'python',[path.resolve('e2e/fixtures/demand_database.py')],{cwd:process.cwd(),env:process.env,input:JSON.stringify({password:providerAccount.password}),encoding:'utf8'})
 expect(fixture.status).toBe(0)
 const data=JSON.parse(fixture.stdout)
 const context=await browser.newContext({viewport:{width,height:900}})
 try{
  const page=await context.newPage()
  await signIn(page,data.customer_email,providerAccount.password,'My requirements')
  await page.goto('/#kyc')
  await expect(page.getByRole('heading',{name:'Customer verification',exact:true})).toBeVisible()
  await expect(page.getByRole('status').filter({hasText:'Customer verification requirements are awaiting approved setup'})).toBeVisible()
  await expect(page.getByRole('button',{name:'Start customer verification',exact:true})).toHaveCount(0)
  expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true)
  await page.screenshot({path:testInfo.outputPath(`customer-verification-${width}.png`),fullPage:true})
 }finally{await context.close()}
})
