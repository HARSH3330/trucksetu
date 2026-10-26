// Explicit opt-in REAL Google checks. Never run automatically in CI; no cloud settings changed.
import{test,expect}from'@playwright/test'
import{readFileSync,writeFileSync}from'node:fs'
const workspace='C:/Users/harsh/Documents/Codex/2026-10-21/read-docs-project-handoff-md-and'
test.skip(process.env.E2E_REAL_GOOGLE_MAPS!=='true','Real Google checks require explicit local opt-in and configured restricted browser key')
test('real Google map/network and authenticated local draft',async({page})=>{
 const failures:object[]=[],googleErrors:string[]=[],requests=new Set<string>()
 const sanitize=(s:string)=>s.replace(/AIza[\w-]+/g,'[REDACTED_BROWSER_KEY]').replace(/([?&]key=)[^&\s]+/g,'$1[REDACTED]')
 page.on('request',r=>{const u=new URL(r.url());if(/(^|\.)(googleapis|gstatic|google)\.com$/.test(u.hostname))requests.add(u.hostname)})
 page.on('requestfailed',r=>{const u=new URL(r.url());if(/google|gstatic/.test(u.hostname))failures.push({host:u.hostname,path:u.pathname,error:sanitize(r.failure()?.errorText||'unknown')})})
 page.on('console',m=>{if(m.type()==='error'&&/Google Maps|RefererNotAllowed|BillingNotEnabled|ApiNotActivated|InvalidKey|MapId/i.test(m.text()))googleErrors.push(sanitize(m.text()))})
 const actor=JSON.parse(readFileSync(workspace+'/private/maps-local-actors.json','utf8').replace(/^\uFEFF/,''))
 await page.goto('/');await page.getByRole('button',{name:'Sign in',exact:true}).click();await page.getByLabel('Email address',{exact:true}).fill(actor.customer_email);await page.getByLabel('Password',{exact:true}).fill('MapsLocalE2E2026!');await page.getByRole('dialog',{name:'Welcome back'}).locator('form').getByRole('button',{name:'Sign in',exact:true}).click();await expect(page.getByRole('heading',{name:'My requirements',exact:true})).toBeVisible();await page.getByRole('button',{name:'Resume draft',exact:true}).click()
 await expect(page.getByLabel('Delivery address — private',{exact:true})).toHaveValue(/Connaught Place/);await page.getByRole('button',{name:'Load map & address search',exact:true}).click();await expect(page.getByRole('button',{name:'Destination pin',exact:true})).toBeVisible();await expect(page.getByRole('link',{name:'Terms (opens in new tab)',exact:true})).toBeVisible()
 await page.locator('.demand-map-controls').screenshot({path:workspace+'/outputs/2026-10-25-real-google-map-desktop.png'})
 expect(googleErrors).toEqual([]);expect(requests.size).toBeGreaterThan(0)
 writeFileSync(workspace+'/outputs/2026-10-25-real-google-network.json',JSON.stringify({classification:'REAL_GOOGLE_API_AND_REAL_ISOLATED_LOCAL_AUTH_DATABASE',origin:'http://127.0.0.1:5173',googleRequestHosts:[...requests],googleErrors,failedRequests:failures,draftAddressRestored:true,realMapMarkerVisible:true,attributionVisible:true,credentialsPrinted:false},null,2))
})
