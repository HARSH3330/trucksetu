// ALL Google/auth/API boundaries below are simulations. Never real billing or KYC.
import {test,expect} from '@playwright/test'
async function googleFixture(page:import('@playwright/test').Page){
 await page.route('https://maps.googleapis.com/**',r=>r.abort())
 await page.addInitScript(()=>{
  class FakeMap{
   el:HTMLElement;handler:((e:{latLng:{lat:()=>number;lng:()=>number}})=>void)|null=null
   constructor(el:HTMLElement){this.el=el;el.textContent='SIMULATED map. No Google request.';const b=document.createElement('button');b.type='button';b.textContent='Place synthetic pin';b.onclick=()=>this.handler?.({latLng:{lat:()=>28.62,lng:()=>77.22}});el.append(b)}
   setCenter(){} setZoom(){} addListener(_n:string,cb:typeof this.handler){this.handler=cb;return{remove:()=>{this.handler=null}}}
  }
  class FakeMarker extends HTMLElement{position:{lat:number;lng:number};map:FakeMap|null;constructor(o:{position:{lat:number;lng:number};map:FakeMap}){super();this.position=o.position;this.map=o.map}}
  customElements.define('fake-map-marker',FakeMarker)
  const w=window as unknown as {releaseDelayed:()=>void}
  w.releaseDelayed=()=>{}
  const place=(label:string,city:string,lat:number,lng:number,delayed=false)=>({formattedAddress:label,location:{lat:()=>lat,lng:()=>lng},addressComponents:[{longText:city,types:['locality']}],fetchFields:()=>delayed?new Promise(resolve=>{w.releaseDelayed=()=>resolve({})}):Promise.resolve({})})
  const prediction=(id:string,label:string,make:()=>unknown)=>({placePrediction:{placeId:id,text:{text:label},mainText:{text:label},secondaryText:{text:'Synthetic suggestion'},toPlace:make}})
  const fetchAutocompleteSuggestions=async({input}:{input:string})=>{
   const text=input.toLowerCase()
   if(text.includes('fail'))throw new Error('Simulated billing failure')
   if(text.includes('delay'))return {suggestions:[prediction('delayed','Delayed synthetic address',()=>place('Delayed synthetic address','Delhi',28.6,77.2,true))]}
   if(text.includes('deliver'))return {suggestions:[prediction('drop','Fictional delivery street, Noida',()=>place('Fictional delivery street, Noida','Noida',28.55,77.4))]}
   return {suggestions:[prediction('pickup','Fictional pickup street, Delhi',()=>place('Fictional pickup street, Delhi','Delhi',28.61,77.2))]}
  }
  Object.assign(window,{google:{maps:{importLibrary:async(name:string)=>name==='maps'?{Map:FakeMap}:name==='places'?{AutocompleteSuggestion:{fetchAutocompleteSuggestions},AutocompleteSessionToken:class{}}:{AdvancedMarkerElement:FakeMarker}}}})
 })
}
async function choose(page:import('@playwright/test').Page,label:string,typed:string,option:string){
 await page.getByLabel(label,{exact:true}).fill(typed)
 await page.getByRole('option',{name:new RegExp(option)}).click()
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
 await page.goto('/e2e/maps-harness.html',{waitUntil:'domcontentloaded'})
 await expect(page.getByText('SIMULATED map',{exact:false})).toHaveCount(0)
 await choose(page,'Pickup address — private','Fictional pick','Fictional pickup street')
 await expect(page.getByLabel('Pickup address — private',{exact:true})).toHaveValue('Fictional pickup street, Delhi')
 await expect(page.getByLabel('Pickup city or area',{exact:true})).toHaveValue('Delhi')
 await expect(page.getByText('SIMULATED map',{exact:false})).toBeVisible()
 await choose(page,'Delivery address — private','Fictional deliver','Fictional delivery street')
 await expect(page.getByLabel('Delivery city or area',{exact:true})).toHaveValue('Noida')
 await page.getByRole('button',{name:'Place synthetic pin',exact:true}).click();await expect(page.getByRole('alert')).toContainText('Pin changed')
 await page.getByRole('button',{name:'Confirm pickup address matches pin',exact:true}).click()
 await page.getByRole('button',{name:'Move pickup pin north',exact:true}).click();await page.getByRole('button',{name:'Confirm pickup address matches pin',exact:true}).click()
 await page.getByRole('button',{name:'Save draft',exact:true}).click();await expect(page.getByText('Draft saved to your account.',{exact:false})).toBeVisible();expect(draft!['pickup_lat']).toBe('28.6201');expect(draft!['pickup_pin_confirmed']).toBe(true)
 expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true)
 await page.screenshot({path:info.outputPath('map-form-'+width+'.png'),fullPage:true})
 await goodsAndReview(page);await page.getByRole('checkbox',{name:'I have reviewed these details and want to publish this requirement.',exact:true}).check();await page.getByRole('button',{name:'Publish requirement',exact:true}).click()
 await expect(page.locator('body')).toHaveAttribute('data-published','true');expect(published!['pickup_location']).toEqual({lat:28.6201,lng:77.22});expect(published!['destination_location']).toEqual({lat:28.55,lng:77.4});expect(published).not.toHaveProperty('distance_km')
})
test('keyboard users can choose a suggestion',async({page})=>{
 await googleFixture(page);await page.goto('/e2e/maps-harness.html',{waitUntil:'domcontentloaded'})
 const field=page.getByLabel('Pickup address — private',{exact:true});await field.fill('Fictional pick')
 await expect(page.getByRole('option',{name:/Fictional pickup street/})).toBeVisible()
 await field.press('ArrowDown');await expect(field).toHaveAttribute('aria-activedescendant',/pickup-address-suggestions-0/);await field.press('Enter')
 await expect(field).toHaveValue('Fictional pickup street, Delhi')
 await field.fill('Fictional pick again');await expect(page.getByRole('listbox')).toBeVisible();await field.press('Escape');await expect(page.getByRole('listbox')).toHaveCount(0)
})
test('simulated billing failure preserves manual entry and clears stale pin',async({page})=>{
 await googleFixture(page);let published:Record<string,unknown>|null=null
 await page.route('**/api/v1/demands',async r=>{published=r.request().postDataJSON();await r.fulfill({status:201,json:{id:'synthetic-manual'}})})
 await page.goto('/e2e/maps-harness.html',{waitUntil:'domcontentloaded'});await choose(page,'Pickup address — private','Fictional pick','Fictional pickup street');await page.getByLabel('Pickup address — private',{exact:true}).fill('Manually corrected private street');await expect(page.getByRole('button',{name:'Remove pickup pin',exact:true})).toHaveCount(0)
 await page.getByLabel('Delivery address — private',{exact:true}).fill('Simulate fail here');await expect(page.getByRole('status').filter({hasText:'unavailable'})).toBeVisible()
 for(const [label,value] of [['Pickup city or area','Delhi'],['Delivery city or area','Noida'],['Delivery address — private','Manual destination street']])await page.getByLabel(label,{exact:true}).fill(value)
 await goodsAndReview(page);await page.getByRole('checkbox',{name:'I have reviewed these details and want to publish this requirement.',exact:true}).check();await page.getByRole('button',{name:'Publish requirement',exact:true}).click();await expect(page.locator('body')).toHaveAttribute('data-published','true');expect(published!['pickup_location']).toBeNull();expect(published!['destination_location']).toBeNull()
})

test('simulated SDK/network outage keeps manual submission usable',async({page})=>{
 await page.route('https://maps.googleapis.com/**',async r=>{await new Promise(resolve=>setTimeout(resolve,250));await r.abort()})
 let payload:Record<string,unknown>|null=null
 await page.route('**/api/v1/demands',async r=>{payload=r.request().postDataJSON();await r.fulfill({status:201,json:{id:'synthetic-offline'}})})
 await page.goto('/e2e/maps-harness.html',{waitUntil:'domcontentloaded'})
 await page.getByLabel('Pickup address — private',{exact:true}).fill('Fictional manual pickup street');await expect(page.getByRole('status').filter({hasText:'unavailable'})).toBeVisible()
 for(const [label,value] of [['Pickup city or area','Delhi'],['Delivery city or area','Noida'],['Delivery address — private','Fictional manual destination street']])await page.getByLabel(label,{exact:true}).fill(value)
 await goodsAndReview(page);await page.getByRole('checkbox',{name:'I have reviewed these details and want to publish this requirement.',exact:true}).check();await page.getByRole('button',{name:'Publish requirement',exact:true}).click();await expect(page.locator('body')).toHaveAttribute('data-published','true');expect(payload!['pickup_location']).toBeNull();expect(payload!['destination_location']).toBeNull();expect(payload).not.toHaveProperty('distance_km')
})

test('late Places result cannot overwrite a later manual city edit',async({page})=>{
 await googleFixture(page);await page.goto('/e2e/maps-harness.html',{waitUntil:'domcontentloaded'})
 await choose(page,'Pickup address — private','Fictional pick','Fictional pickup street');await expect(page.getByLabel('Pickup city or area',{exact:true})).toHaveValue('Delhi')
 await choose(page,'Pickup address — private','Delayed place','Delayed synthetic address')
 await page.getByLabel('Pickup city or area',{exact:true}).fill('Gurugram')
 await page.evaluate(()=>(window as unknown as {releaseDelayed:()=>void}).releaseDelayed())
 await expect(page.getByLabel('Pickup city or area',{exact:true})).toHaveValue('Gurugram');await expect(page.getByRole('button',{name:'Remove pickup pin',exact:true})).toHaveCount(0)
})
