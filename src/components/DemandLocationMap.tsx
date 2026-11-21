import {useState} from 'react'
import LocationMap from './LocationMap'
import {moveLocation,confirmLocation,clearLocation,pendingLocation,type Endpoint,type LocationFields} from '../lib/demand-location'

const NAMES:Record<Endpoint,string>={pickup:'pickup',destination:'destination'}

/** Map shown below the address fields once a Google suggestion has placed a pin. */
export default function DemandLocationMap({form,onChange}:{form:LocationFields;onChange:(p:Record<string,string|boolean>)=>void}){
 const [active,setActive]=useState<Endpoint>('pickup')
 const points={pickup:pendingLocation(form,'pickup'),destination:pendingLocation(form,'destination')}
 if(!points.pickup&&!points.destination)return null
 const both=Boolean(points.pickup&&points.destination)
 return <section className="demand-map-controls" aria-label="Pickup and drop map">
  <h3>Check the pins on the map</h3>
  <p>Drag a pin, or tap the map, to mark the exact gate or loading point. Map searches are shared with Google.</p>
  {both&&<fieldset className="demand-pin-choice"><legend>Pin to adjust</legend>{(['pickup','destination'] as const).map(end=><label className="demand-check" key={end}><input type="radio" name="map-endpoint" checked={active===end} onChange={()=>setActive(end)}/>{end==='pickup'?'Pickup':'Drop'}</label>)}</fieldset>}
  <LocationMap points={points} onMove={(end,point)=>onChange(moveLocation(end,point))} onTap={point=>onChange(moveLocation(both?active:points.pickup?'pickup':'destination',point))}/>
  {(['pickup','destination'] as const).map(end=>{const p=points[end];return p&&<div key={end} className="demand-pin-review"><p>{end==='pickup'?'Pickup':'Drop'} pin: {p.lat.toFixed(6)}, {p.lng.toFixed(6)}</p>
   <div className="demand-pin-actions"><span>Nudge</span>{([['north','↑',0.0001,0],['south','↓',-0.0001,0],['east','→',0,0.0001],['west','←',0,-0.0001]] as const).map(([name,arrow,a,b])=><button type="button" className="secondary demand-nudge" key={name} aria-label={`Move ${NAMES[end]} pin ${name}`} title={`Move ${name}`} onClick={()=>onChange(moveLocation(end,{lat:Math.max(-90,Math.min(90,p.lat+a)),lng:Math.max(-180,Math.min(180,p.lng+b))}))}>{arrow}</button>)}</div>
   {form[end+'_pin_confirmed']!==true&&<p role="alert">Pin changed. Check the {NAMES[end]} address, then confirm it matches this pin, or remove the pin.</p>}
   {form[end+'_pin_confirmed']!==true&&<button type="button" disabled={!String(form[end+'_address']||'').trim()||!String(form[end+'_city']||'').trim()} onClick={()=>onChange(confirmLocation(end))}>Confirm {NAMES[end]} address matches pin</button>}
   <button type="button" className="secondary" onClick={()=>onChange(clearLocation(end))}>Remove {NAMES[end]} pin</button></div>})}
 </section>
}
