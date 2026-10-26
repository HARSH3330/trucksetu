import {useEffect,useRef,useState} from 'react'
import {loadGoogleMaps,mapFailure,type MapInstance,type MapLibraries,type MarkerInstance,type SelectPlaceEvent} from '../lib/google-maps'
import {moveLocation,confirmLocation,clearLocation,pendingLocation,type Endpoint,type LocationFields,type MapPoint} from '../lib/demand-location'
export default function DemandLocationMap({form,onChange}:{form:LocationFields;onChange:(p:Record<string,string|boolean>)=>void}){
 const [open,setOpen]=useState(false),[attempt,setAttempt]=useState(0),[status,setStatus]=useState(''),[ready,setReady]=useState(false),[active,setActive]=useState<Endpoint>('pickup')
 const latest=useRef({form,onChange,active});latest.current={form,onChange,active}
 const canvas=useRef<HTMLDivElement>(null),searches=useRef<HTMLDivElement>(null),map=useRef<MapInstance|null>(null),libs=useRef<MapLibraries|null>(null),markers=useRef<Partial<Record<Endpoint,MarkerInstance>>>({})
 useEffect(()=>{
  if(!open||!canvas.current||!searches.current)return
  let alive=true;const clean:(()=>void)[]=[];const generations={pickup:0,destination:0}
  setReady(false);setStatus('Loading optional map and address search…')
  const fail=()=>{if(alive){setReady(false);setStatus(mapFailure)}}
  window.addEventListener('transivox-maps-error',fail);clean.push(()=>window.removeEventListener('transivox-maps-error',fail))
  void loadGoogleMaps().then(sdk=>{
   if(!alive)return
   libs.current=sdk
   map.current=new sdk.maps.Map(canvas.current!,{center:{lat:22.5,lng:79},zoom:4,mapId:import.meta.env.VITE_GOOGLE_MAPS_MAP_ID||'DEMO_MAP_ID',gestureHandling:'cooperative',streetViewControl:false,mapTypeControl:false})
   const listener=map.current.addListener('click',e=>{if(e.latLng)latest.current.onChange(moveLocation(latest.current.active,{lat:e.latLng.lat(),lng:e.latLng.lng()}))});clean.push(()=>listener.remove())
   for(const end of ['pickup','destination'] as const){
    const label=document.createElement('label');label.textContent=end==='pickup'?'Search pickup with Google':'Search destination with Google'
    const input=new sdk.places.PlaceAutocompleteElement({includedRegionCodes:['in']});input.setAttribute('aria-label',label.textContent);input.setAttribute('placeholder','Search an address or place');label.append(input);searches.current!.append(label)
    const error=()=>{generations[end]++;fail()}
    const changed=()=>{generations[end]++;latest.current.onChange(clearLocation(end))}
    const select=async(event:Event)=>{
     const sequence=++generations[end],snapshot=JSON.stringify(['address','city','lat','lng','pin_confirmed'].map(key=>latest.current.form[end+'_'+key]))
     try{
      const place=(event as SelectPlaceEvent).placePrediction.toPlace();await place.fetchFields({fields:['formattedAddress','location','addressComponents']})
      if(!alive||sequence!==generations[end]||JSON.stringify(['address','city','lat','lng','pin_confirmed'].map(key=>latest.current.form[end+'_'+key]))!==snapshot)return
      if(!place.location||!place.formattedAddress)throw new Error()
      const city=place.addressComponents?.find(c=>c.types.includes('locality'))?.longText||place.addressComponents?.find(c=>c.types.includes('postal_town'))?.longText||String(latest.current.form[end+'_city']||'')
      latest.current.onChange({...moveLocation(end,{lat:place.location.lat(),lng:place.location.lng()}),...confirmLocation(end),[end+'_address']:place.formattedAddress,[end+'_city']:city});setStatus('Address and pin selected. Check the private address fields before continuing.')
     }catch{if(alive&&sequence===generations[end]){latest.current.onChange(clearLocation(end));fail()}}
    }
    input.addEventListener('gmp-select',select);input.addEventListener('gmp-error',error);input.addEventListener('input',changed)
    clean.push(()=>{generations[end]++;input.removeEventListener('gmp-select',select);input.removeEventListener('gmp-error',error);input.removeEventListener('input',changed);label.remove()})
   }
   setReady(true);setStatus('Choose an address, then check or adjust its pin. No route distance is calculated.')
  }).catch(fail)
  return()=>{alive=false;clean.forEach(f=>f());Object.values(markers.current).forEach(m=>{if(m)m.map=null});markers.current={};map.current=null;libs.current=null;if(canvas.current)canvas.current.replaceChildren()}
 },[open,attempt])
 useEffect(()=>{
  if(!ready||!map.current||!libs.current)return
  let center:MapPoint|null=null
  for(const end of ['pickup','destination'] as const){
   const point=pendingLocation(form,end),old=markers.current[end]
   if(!point){if(old)old.map=null;delete markers.current[end];continue}
   center=point
   if(old)old.position=point
   else{
    const marker=new libs.current.marker.AdvancedMarkerElement({map:map.current,position:point,gmpDraggable:true,title:end==='pickup'?'Pickup pin':'Destination pin'})
    marker.addEventListener('gmp-dragend',()=>{const p=marker.position;if(p){const point={lat:typeof p.lat==='function'?p.lat():p.lat,lng:typeof p.lng==='function'?p.lng():p.lng};latest.current.onChange(moveLocation(end,point))}})
    markers.current[end]=marker
   }
  }
  const target=pendingLocation(form,active)||center;if(target){map.current.setCenter(target);map.current.setZoom(14)}
 },[form,active,ready])
 return <section className="demand-map-controls" aria-label="Optional pickup and destination map"><h3>Check locations on a map — optional</h3><p>Manual addresses below always work. If a search has no suggestions, clear it or enter the address manually. Loading Google Maps shares map searches with Google.</p>
 {!open?<button type="button" className="secondary" onClick={()=>setOpen(true)}>Load map & address search</button>:<>
 <p role="status">{status}</p>{!ready&&!status.startsWith('Loading')&&<button type="button" className="secondary" onClick={()=>setAttempt(x=>x+1)}>Retry map</button>}
 <div ref={searches} className="demand-map-searches"/>
 <fieldset disabled={!ready}><legend>Choose the pin to place or adjust</legend>{(['pickup','destination'] as const).map(end=><label className="demand-check" key={end}><input type="radio" name="map-endpoint" checked={active===end} onChange={()=>setActive(end)}/>{end==='pickup'?'Pickup':'Destination'}</label>)}</fieldset>
 <div ref={canvas} className="demand-map-canvas" aria-label="Google map preview"/>
 <p>Tap the map to place the selected pin, or drag it. Google map attribution and controls remain visible.</p>
 </>}
 {(['pickup','destination'] as const).map(end=>{const p=pendingLocation(form,end);return p&&<div key={end} className="demand-pin-review"><p>{end==='pickup'?'Pickup':'Destination'} pin: {p.lat.toFixed(6)}, {p.lng.toFixed(6)}</p>
 <div className="demand-pin-actions">{([['north',0.0001,0],['south',-0.0001,0],['east',0,0.0001],['west',0,-0.0001]] as const).map(([name,a,b])=><button type="button" className="secondary" key={name} onClick={()=>onChange(moveLocation(end,{lat:Math.max(-90,Math.min(90,p.lat+a)),lng:Math.max(-180,Math.min(180,p.lng+b))}))}>Move {end} pin {name}</button>)}</div>
 {form[end+'_pin_confirmed']!==true&&<p role="alert">Pin changed. Check the {end} address, then confirm it matches this pin, or remove the pin.</p>}
 <button type="button" disabled={!String(form[end+'_address']||'').trim()||!String(form[end+'_city']||'').trim()} onClick={()=>onChange(confirmLocation(end))}>Confirm {end} address matches pin</button><button type="button" className="secondary" onClick={()=>onChange(clearLocation(end))}>Remove {end} pin</button></div>})}
 </section>
}
