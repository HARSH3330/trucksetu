// ALL Google/auth/API boundaries below are simulations. Never real billing or KYC.
import {test,expect} from '@playwright/test'
async function googleFixture(page:import('@playwright/test').Page){
 await page.route('https://maps.googleapis.com/**',r=>r.abort())
 await page.addInitScript(()=>{
  let count=0
  class FakeMap{
   el:HTMLElement;handler:((e:{latLng:{lat:()=>number;lng:()=>number}})=>void)|null=null
   constructor(el:HTMLElement){this.el=el;el.textContent='SIMULATED map. No Google request.';const b=document.createElement('button');b.type='button';b.textContent='Place synthetic pin';b.onclick=()=>this.handler?.({latLng:{lat:()=>28.62,lng:()=>77.22}});el.append(b)}
   setCenter(){} setZoom(){} addListener(_n:string,cb:typeof this.handler){this.handler=cb;return{remove:()=>{this.handler=null}}}
  }
  class FakeAutocomplete extends HTMLElement{
   constructor(){super();const end=count++%2===0?'pickup':'destination';const b=document.createElement('button');b.type='button';b.textContent='Select synthetic '+end;b.setAttribute('aria-label',b.textContent);b.onclick=()=>{const e=new Event('gmp-select');Object.assign(e,{placePrediction:{toPlace:()=>({formattedAddress:end==='pickup'?'Fictional pickup street, Delhi':'Fictional delivery street, Noida',location:{lat:()=>end==='pickup'?28.61:28.55,lng:()=>end==='pickup'?77.2:77.4},addressComponents:[{longText:end==='pickup'?'Delhi':'Noida',types:['locality']}],fetchFields:async()=>({})})}});this.dispatchEvent(e)};this.append(b);const fail=document.createElement('button');fail.type='button';fail.textContent='Simulate '+end+' billing failure';fail.onclick=()=>this.dispatchEvent(new Event('gmp-error'));this.append(fail);let release=()=>{};const late=document.createElement('button');late.type='button';late.textContent='Select delayed '+end;late.setAttribute('aria-label',late.textContent);late.onclick=()=>{const e=new Event('gmp-select');Object.assign(e,{placePrediction:{toPlace:()=>({formattedAddress:'Delayed synthetic address',location:{lat:()=>28.6,lng:()=>77.2},addressComponents:[{longText:'Delhi',types:['locality']}],fetchFields:()=>new Promise(resolve=>{release=()=>resolve({})})})}});this.dispatchEvent(e)};this.append(late);const finish=document.createElement('button');finish.type='button';finish.textContent='Finish delayed '+end;finish.setAttribute('aria-label',finish.textContent);finish.onclick=()=>release();this.append(finish)}
  }
  class FakeMarker extends HTMLElement{position:{lat:number;lng:number};map:FakeMap|null;constructor(o:{position:{lat:number;lng:number};map:FakeMap}){super();this.position=o.position;this.map=o.map}}
  customElements.define('fake-place-autocomplete',FakeAutocomplete);customElements.define('fake-map-marker',FakeMarker)
  Object.assign(window,{google:{maps:{importLibrary:async(name:string)=>name==='maps'?{Map:FakeMap}:name==='places'?{PlaceAutocompleteElement:FakeAutocomplete}:{AdvancedMarkerElement:FakeMarker}}}})
 })
}
async function goodsAndReview(page:import('@playwright/test').Page){
 const date=(n:number)=>{const d=new Date(Date.now()+n*86400000);return new Date(d.getTime()-d.getTimezoneOffset()*60000).toISOString().slice(0,16)}
 for(const [label,value] of [['Earliest pickup — local time',date(2)],['Latest pickup — local time',date(3)],['Delivery deadline — local time',date(4)]])await page.getByLabel(label,{exact:true}).fill(value)
 await page.getByRole('button',{name:'Continue',exact:true}).click()
 for(const [label,value] of [['Goods category','Furniture'],['Describe the goods','Synthetic harmless cartons'],['Total weight','1000'],['Length (metres)','1'],['Width (metres)','1'],['Height (metres)','1']])await page.getByLabel(label,{exact:true}).fill(value)
 await page.getByRole('button',{name:'Continue',exact:true}).click()
}
for(const width of [1440,390])test('simulated Places/pins/drafts/publication at '+width+'px',async({page},info)=>{
 await page.setViewportSize({width,height:950});await googleFixture(page)
 let draft:Record<string,unknown>|null=null,published:Record<string,unknown>|null=null
 await page.route('**/api/v1/**',async route=>{const req=route.request();if(req.url().includes('/demands/drafts')){draft=req.postDataJSON().payload;await route.fulfill({json:{id:'synthetic-draft',version:1}})}else if(req.url().endsWith('/demands')){published=req.postDataJSON();await route.fulfill({status:201,json:{id:'synthetic-demand'}})}else await route.fulfill({status:404,json:{detail:'Synthetic harness only'}})})
 await page.goto('/e2e/maps-harness.html',{waitUntil:'domcontentloaded'});await page.getByRole('button',{name:'Load map & address search',exact:true}).click()
 await page.getByRole('button',{name:'Select synthetic pickup',exact:true}).click();await page.getByRole('button',{name:'Select synthetic destination',exact:true}).click()
 await expect(page.getByLabel('Pickup address — private',{exact:true})).toHaveValue('Fictional pickup street, Delhi')
 await page.getByRole('button',{name:'Place synthetic pin',exact:true}).click();await expect(page.getByRole('alert')).toContainText('Pin changed')
 await page.getByRole('button',{name:'Confirm pickup address matches pin',exact:true}).click()
 await page.getByRole('button',{name:'Move pickup pin north',exact:true}).click();await page.getByRole('button',{name:'Confirm pickup address matches pin',exact:true}).click()
 await page.getByRole('button',{name:'Save draft',exact:true}).click();await expect(page.getByText('Draft saved to your account.',{exact:false})).toBeVisible();expect(draft!['pickup_lat']).toBe('28.6201');expect(draft!['pickup_pin_confirmed']).toBe(true)
 expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true)
 await page.screenshot({path:info.outputPath('map-form-'+width+'.png'),fullPage:true})
 await goodsAndReview(page);await page.getByRole('checkbox',{name:'I have reviewed these details and want to publish this requirement.',exact:true}).check();await page.getByRole('button',{name:'Publish requirement',exact:true}).click()
 await expect(page.locator('body')).toHaveAttribute('data-published','true');expect(published!['pickup_location']).toEqual({lat:28.6201,lng:77.22});expect(published!['destination_location']).toEqual({lat:28.55,lng:77.4});expect(published).not.toHaveProperty('distance_km')
})
test('simulated billing failure preserves manual entry and clears stale pin',async({page})=>{
 await googleFixture(page);let published:Record<string,unknown>|null=null
 await page.route('**/api/v1/demands',async r=>{published=r.request().postDataJSON();await r.fulfill({status:201,json:{id:'synthetic-manual'}})})
 await page.goto('/e2e/maps-harness.html',{waitUntil:'domcontentloaded'});await page.getByRole('button',{name:'Load map & address search',exact:true}).click();await page.getByRole('button',{name:'Select synthetic pickup',exact:true}).click();await page.getByLabel('Pickup address — private',{exact:true}).fill('Manually corrected private street');await expect(page.getByRole('button',{name:'Remove pickup pin',exact:true})).toHaveCount(0)
 await page.getByRole('button',{name:'Simulate pickup billing failure',exact:true}).click();await expect(page.getByRole('status')).toContainText('billing')
 for(const [label,value] of [['Pickup city or area','Delhi'],['Delivery city or area','Noida'],['Delivery address — private','Manual destination street']])await page.getByLabel(label,{exact:true}).fill(value)
 await goodsAndReview(page);await page.getByRole('checkbox',{name:'I have reviewed these details and want to publish this requirement.',exact:true}).check();await page.getByRole('button',{name:'Publish requirement',exact:true}).click();await expect(page.locator('body')).toHaveAttribute('data-published','true');expect(published!['pickup_location']).toBeNull();expect(published!['destination_location']).toBeNull()
})

test('simulated SDK/network outage keeps manual submission usable',async({page})=>{
 await page.route('https://maps.googleapis.com/**',async r=>{await new Promise(resolve=>setTimeout(resolve,250));await r.abort()})
 let payload:Record<string,unknown>|null=null
 await page.route('**/api/v1/demands',async r=>{payload=r.request().postDataJSON();await r.fulfill({status:201,json:{id:'synthetic-offline'}})})
 await page.goto('/e2e/maps-harness.html',{waitUntil:'domcontentloaded'});await page.getByRole('button',{name:'Load map & address search',exact:true}).click();await expect(page.getByRole('status')).toContainText('unavailable');await expect(page.getByRole('button',{name:'Retry map',exact:true})).toBeVisible()
 for(const [label,value] of [['Pickup city or area','Delhi'],['Delivery city or area','Noida'],['Pickup address — private','Fictional manual pickup street'],['Delivery address — private','Fictional manual destination street']])await page.getByLabel(label,{exact:true}).fill(value)
 await goodsAndReview(page);await page.getByRole('checkbox',{name:'I have reviewed these details and want to publish this requirement.',exact:true}).check();await page.getByRole('button',{name:'Publish requirement',exact:true}).click();await expect(page.locator('body')).toHaveAttribute('data-published','true');expect(payload!['pickup_location']).toBeNull();expect(payload!['destination_location']).toBeNull();expect(payload).not.toHaveProperty('distance_km')
})

test('late Places result cannot overwrite a later manual city edit',async({page})=>{
 await googleFixture(page);await page.goto('/e2e/maps-harness.html',{waitUntil:'domcontentloaded'});await page.getByRole('button',{name:'Load map & address search',exact:true}).click();await page.getByRole('button',{name:'Select synthetic pickup',exact:true}).click();await expect(page.getByLabel('Pickup city or area',{exact:true})).toHaveValue('Delhi');await page.getByRole('button',{name:'Select delayed pickup',exact:true}).click();await page.getByLabel('Pickup city or area',{exact:true}).fill('Gurugram');await page.getByRole('button',{name:'Finish delayed pickup',exact:true}).click();await expect(page.getByLabel('Pickup city or area',{exact:true})).toHaveValue('Gurugram');await expect(page.getByRole('button',{name:'Remove pickup pin',exact:true})).toHaveCount(0)
})
