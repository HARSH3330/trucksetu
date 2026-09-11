import {useEffect, useState} from 'react'
import {BadgeCheck, CalendarClock, Check, Plus, ShieldCheck, Truck, UserPlus, UsersRound} from 'lucide-react'
import {ApiError, apiFetch, publicFetch, type ProviderProfile, type VehicleCategory} from '../lib/api'
import './LiveFleet.css'

type Vehicle={id:string;vehicle_category_name:string|null;registration_number:string;body_type:string;maximum_payload_tonnes:string;maximum_volume_m3:string;permit_territories:string[];service_areas:string[];status:string;document_eligible_today:boolean;document_expiries:Record<string,string>}
type Driver={id:string;full_name:string;masked_mobile:string;licence_expires_on:string|null;kyc_status:string;active:boolean}
const initialVehicle={category:'',registration:'',body:'closed',payload:'',length:'',width:'',height:'',territories:'',areas:'',rc:'',insurance:'',fitness:'',pollution:'',permit:''}

export default function LiveFleet(){
  const [profile,setProfile]=useState<ProviderProfile|null>(null)
  const [vehicles,setVehicles]=useState<Vehicle[]>([])
  const [drivers,setDrivers]=useState<Driver[]>([])
  const [categories,setCategories]=useState<VehicleCategory[]>([])
  const [tab,setTab]=useState<'overview'|'vehicle'|'driver'>('overview')
  const [vehicle,setVehicle]=useState(initialVehicle)
  const [driver,setDriver]=useState({email:'',licence:'',expires:''})
  const [state,setState]=useState<'loading'|'ready'|'signed-out'|'unavailable'|'error'>('loading')
  const [message,setMessage]=useState('')

  async function load(){
    setState('loading')
    try{
      const provider=await apiFetch<ProviderProfile>('/providers/me');setProfile(provider)
      const [fleet,people,types]=await Promise.all([apiFetch<Vehicle[]>('/carrier-vehicles'),apiFetch<Driver[]>(`/providers/${provider.id}/drivers`),publicFetch<VehicleCategory[]>('/vehicle-categories')])
      setVehicles(fleet);setDrivers(people);setCategories(types);setVehicle(value=>({...value,category:value.category||types[0]?.id||''}));setState('ready')
    }catch(error){setState(error instanceof ApiError&&error.status===401?'signed-out':error instanceof ApiError&&[403,404].includes(error.status)?'unavailable':'error');setMessage(error instanceof Error?error.message:'Fleet unavailable')}
  }
  useEffect(()=>{void load()},[])
  const set=(key:keyof typeof initialVehicle,value:string)=>setVehicle(current=>({...current,[key]:value}))

  async function addVehicle(event:React.FormEvent){
    event.preventDefault();if(!profile)return;setMessage('Submitting vehicle for manual approval…')
    try{await apiFetch('/carrier-vehicles',{method:'POST',body:JSON.stringify({provider_id:profile.id,vehicle_category_id:vehicle.category,registration_number:vehicle.registration,body_type:vehicle.body,maximum_payload_tonnes:Number(vehicle.payload),internal_length_m:Number(vehicle.length),internal_width_m:Number(vehicle.width),internal_height_m:Number(vehicle.height),permit_territories:vehicle.territories.split(',').map(x=>x.trim()).filter(Boolean),service_areas:vehicle.areas.split(',').map(x=>x.trim()).filter(Boolean),rc_expires_on:vehicle.rc,insurance_expires_on:vehicle.insurance,fitness_expires_on:vehicle.fitness,pollution_expires_on:vehicle.pollution,permit_expires_on:vehicle.permit})});setVehicle({...initialVehicle,category:categories[0]?.id||''});setTab('overview');setMessage('Vehicle submitted for manual approval.');await load()}
    catch(error){setMessage(error instanceof Error?error.message:'Vehicle could not be submitted')}
  }
  async function linkDriver(event:React.FormEvent){
    event.preventDefault();if(!profile)return;setMessage('Linking verified driver…')
    try{await apiFetch(`/providers/${profile.id}/drivers`,{method:'POST',body:JSON.stringify({email:driver.email,licence_number:driver.licence,licence_expires_on:driver.expires})});setDriver({email:'',licence:'',expires:''});setTab('overview');setMessage('Verified driver linked.');await load()}
    catch(error){setMessage(error instanceof Error?error.message:'Driver could not be linked')}
  }

  if(state==='loading')return <main className="page"><div className="empty-state">Loading fleet operations…</div></main>
  if(state==='signed-out')return <main className="page"><div className="empty-state"><b>Sign in required</b><p>Fleet records are private.</p></div></main>
  if(state==='unavailable')return <main className="page"><div className="empty-state"><b>Provider profile required</b><p>{message}</p></div></main>
  if(state==='error'||!profile)return <main className="page"><div className="empty-state"><b>Fleet operations unavailable</b><button onClick={load}>Retry</button></div></main>
  return <main className="page"><div className="page-title"><span className="kicker">PROVIDER OPERATIONS</span><h1>Fleet & drivers</h1><p>{profile.display_name} · KYC {profile.kyc_status}</p></div>{message&&<div className="privacy-banner">{message}</div>}<div className="fleet-tabs"><button className={tab==='overview'?'active':''} onClick={()=>setTab('overview')}>Fleet overview</button><button className={tab==='vehicle'?'active':''} onClick={()=>setTab('vehicle')}><Plus/> Add vehicle</button><button className={tab==='driver'?'active':''} onClick={()=>setTab('driver')}><UserPlus/> Link driver</button></div>
    {tab==='overview'&&<><div className="fleet-summary"><span><Truck/><b>{vehicles.length}</b><small>Registered vehicles</small></span><span><BadgeCheck/><b>{vehicles.filter(x=>x.status==='approved').length}</b><small>Approved vehicles</small></span><span><UsersRound/><b>{drivers.length}</b><small>Linked drivers</small></span><span><ShieldCheck/><b>{vehicles.filter(x=>x.document_eligible_today).length}</b><small>Eligible today</small></span></div><section className="panel"><div className="panel-head"><h3>Vehicles</h3><span className="badge">PRIVATE FLEET</span></div><div className="fleet-list">{vehicles.map(item=><article key={item.id}><span className="fleet-icon"><Truck/></span><div><b>{item.registration_number}</b><small>{item.vehicle_category_name||item.body_type} · {item.maximum_payload_tonnes} t · {item.maximum_volume_m3} m³</small><em>{item.service_areas.join(', ')||'No service areas'}</em></div><span className={`fleet-state ${item.document_eligible_today?'ok':'warn'}`}>{item.status} · {item.document_eligible_today?'documents current':'not dispatch eligible'}</span><details><summary><CalendarClock/> Expiry dates</summary>{Object.entries(item.document_expiries).map(([key,value])=><small key={key}>{key}: {new Date(value).toLocaleDateString('en-IN')}</small>)}</details></article>)}{!vehicles.length&&<div className="empty-state">No vehicles registered yet.</div>}</div></section><section className="panel fleet-drivers"><div className="panel-head"><h3>Linked drivers</h3></div>{drivers.map(item=><article key={item.id}><span><UsersRound/></span><div><b>{item.full_name}</b><small>{item.masked_mobile} · licence expires {item.licence_expires_on?new Date(item.licence_expires_on).toLocaleDateString('en-IN'):'not recorded'}</small></div><span className={`fleet-state ${(item.active && item.kyc_status === 'verified') ? 'ok' : 'warn'}`}>{item.kyc_status} · {item.active?'active':'inactive'}</span></article>)}{!drivers.length&&<div className="empty-state">No verified drivers linked.</div>}</section></>}
    {tab==='vehicle'&&<form className="panel fleet-form" onSubmit={addVehicle}><h3>Register a commercial vehicle</h3><p>Metadata is saved for manual approval. Document file uploads remain deferred.</p><label>Vehicle category<select required value={vehicle.category} onChange={e=>set('category',e.target.value)}>{categories.map(item=><option value={item.id} key={item.id}>{item.name} · max {item.max_capacity_tonnes} t</option>)}</select></label><label>Registration number<input required minLength={5} value={vehicle.registration} onChange={e=>set('registration',e.target.value.toUpperCase())}/></label><label>Body type<select value={vehicle.body} onChange={e=>set('body',e.target.value)}><option value="closed">Closed</option><option value="open">Open</option><option value="container">Container</option></select></label><label>Maximum payload (tonnes)<input required type="number" min="0.001" step="0.001" value={vehicle.payload} onChange={e=>set('payload',e.target.value)}/></label><label>Internal length (m)<input required type="number" min="0.001" step="0.001" value={vehicle.length} onChange={e=>set('length',e.target.value)}/></label><label>Internal width (m)<input required type="number" min="0.001" step="0.001" value={vehicle.width} onChange={e=>set('width',e.target.value)}/></label><label>Internal height (m)<input required type="number" min="0.001" step="0.001" value={vehicle.height} onChange={e=>set('height',e.target.value)}/></label><label>Permit territories<input required value={vehicle.territories} onChange={e=>set('territories',e.target.value)} placeholder="Delhi, Haryana, Rajasthan"/></label><label>Service areas<input required value={vehicle.areas} onChange={e=>set('areas',e.target.value)} placeholder="Delhi NCR, Jaipur"/></label>{([['rc','RC expiry'],['insurance','Insurance expiry'],['fitness','Fitness expiry'],['pollution','Pollution certificate expiry'],['permit','Permit expiry']] as const).map(([key,label])=><label key={key}>{label}<input required type="date" value={vehicle[key]} onChange={e=>set(key,e.target.value)}/></label>)}<button><Check/> Submit vehicle</button></form>}
    {tab==='driver'&&<form className="panel driver-form" onSubmit={linkDriver}><h3>Link an existing verified driver</h3><p>The driver must first create a driver account and complete manual KYC.</p><label>Driver account email<input required type="email" value={driver.email} onChange={e=>setDriver({...driver,email:e.target.value})}/></label><label>Driving licence number<input required minLength={5} value={driver.licence} onChange={e=>setDriver({...driver,licence:e.target.value.toUpperCase()})}/></label><label>Licence expiry<input required type="date" value={driver.expires} onChange={e=>setDriver({...driver,expires:e.target.value})}/></label><button><UserPlus/> Link verified driver</button></form>}
  </main>
}
