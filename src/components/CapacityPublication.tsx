import {useEffect,useState} from 'react'
import {apiFetch,type ProviderProfile} from '../lib/api'

type Vehicle={id:string;vehicle_category_id:string;registration_number:string;status:string;document_eligible_today:boolean;maximum_payload_tonnes:string;maximum_volume_m3:string;permit_territories:string[];service_areas:string[]}
type Driver={id:string;full_name:string;active:boolean;kyc_status:string}
const fields=[
  ['origin_city','Route origin city','text'],['destination_city','Route destination city','text'],
  ['origin_address','Route origin address','text'],['destination_address','Route destination address','text'],
  ['departure_at','Departure start','datetime-local'],['departure_window_end','Departure window end','datetime-local'],['expected_arrival_at','Expected arrival','datetime-local'],
  ['total_capacity_tonnes','Total weight capacity (tonnes)','number'],['available_capacity_tonnes','Available weight (tonnes)','number'],
  ['total_volume_m3','Total volume (m³)','number'],['available_volume_m3','Available volume (m³)','number'],['minimum_booking_tonnes','Minimum booking weight (tonnes)','number'],
  ['price_amount','Route price (INR)','number'],['minimum_acceptable_earning','Minimum acceptable earning (INR)','number'],['maximum_deviation_km','Maximum deviation (km)','number'],['maximum_added_time_minutes','Maximum added time (minutes)','number'],
] as const

export default function CapacityPublication(){
  const [profile,setProfile]=useState<ProviderProfile|null>(null)
  const [vehicles,setVehicles]=useState<Vehicle[]>([]),[drivers,setDrivers]=useState<Driver[]>([])
  const [vehicleId,setVehicleId]=useState(''),[driverId,setDriverId]=useState('')
  const [values,setValues]=useState<Record<string,string>>({}),[cargo,setCargo]=useState(''),[stops,setStops]=useState(''),[basis,setBasis]=useState('per_tonne')
  const [state,setState]=useState<'loading'|'ready'|'error'>('loading'),[busy,setBusy]=useState(false),[message,setMessage]=useState('')
  async function load(){
    setState('loading')
    try{
      const account=await apiFetch<ProviderProfile>('/providers/me');setProfile(account)
      const [fleet,people]=await Promise.all([apiFetch<Vehicle[]>('/carrier-vehicles'),apiFetch<Driver[]>(`/providers/${account.id}/drivers`)])
      const approved=fleet.filter(item=>item.status==='approved'&&item.document_eligible_today),verified=people.filter(item=>item.active&&item.kyc_status==='verified')
      setVehicles(approved);setDrivers(verified);setVehicleId(approved[0]?.id||'');setDriverId(verified[0]?.id||'');setState('ready')
    }catch(error){setState('error');setMessage(error instanceof Error?error.message:'Publication setup unavailable')}
  }
  useEffect(()=>{void load()},[])
  async function publish(event:React.FormEvent){
    event.preventDefault();const vehicle=vehicles.find(item=>item.id===vehicleId)
    if(busy||!vehicle||!profile||!driverId)return
    setBusy(true);setMessage('')
    try{
      const payload:Record<string,unknown>={...values,provider_id:profile.id,carrier_vehicle_id:vehicle.id,vehicle_category_id:vehicle.vehicle_category_id,driver_id:driverId,allowed_cargo_types:cargo.split(',').map(item=>item.trim()).filter(Boolean),intermediate_cities:stops.split(',').map(item=>item.trim()).filter(Boolean),price_basis:basis,permit_territories:vehicle.permit_territories,service_areas:vehicle.service_areas}
      for(const field of ['departure_at','departure_window_end','expected_arrival_at'])payload[field]=new Date(values[field]).toISOString()
      payload.maximum_added_time_minutes=Number(values.maximum_added_time_minutes)
      const result=await apiFetch<{id:string}>('/available-routes',{method:'POST',body:JSON.stringify(payload)})
      setMessage(`Published route ${result.id}`)
    }catch(error){setMessage(error instanceof Error?error.message:'Publication failed')}
    finally{setBusy(false)}
  }
  return <details className="panel"><summary>Publish shared capacity</summary>
    {message&&<p role="status">{message}</p>}{state==='loading'?<p>Loading your fleet…</p>:state==='error'?<button onClick={()=>void load()}>Retry publication setup</button>:profile?.kyc_status!=='verified'||!profile.active?<p>Complete provider re-verification before publishing routes.</p>:!vehicles.length||!drivers.length?<p>An approved vehicle with current documents and a verified active driver are required. Open Fleet &amp; drivers to complete them.</p>:<form aria-label="Publish shared capacity" className="fields" onSubmit={publish}>
      <p>Publish actual spare space. Future-date document eligibility is checked again by the API.</p>
      <label>Route vehicle<select value={vehicleId} disabled={busy} onChange={event=>setVehicleId(event.target.value)}>{vehicles.map(item=><option value={item.id} key={item.id}>{item.registration_number} · {item.maximum_payload_tonnes} t · {item.maximum_volume_m3} m³</option>)}</select></label>
      <label>Route driver<select value={driverId} disabled={busy} onChange={event=>setDriverId(event.target.value)}>{drivers.map(item=><option value={item.id} key={item.id}>{item.full_name}</option>)}</select></label>
      {fields.map(([key,label,type])=><label key={key}>{label}<input required disabled={busy} type={type} min={type==='number'?'0':undefined} step={key==='maximum_added_time_minutes'?'1':type==='number'?'0.001':undefined} maxLength={type==='text'?500:undefined} value={values[key]||''} onChange={event=>setValues({...values,[key]:event.target.value})}/></label>)}
      <label>Intermediate route cities (ordered, comma separated)<input disabled={busy} maxLength={2000} value={stops} onChange={event=>setStops(event.target.value)}/></label>
      <label>Allowed cargo types<input required disabled={busy} maxLength={2000} value={cargo} onChange={event=>setCargo(event.target.value)}/></label>
      <label>Price basis<select disabled={busy} value={basis} onChange={event=>setBasis(event.target.value)}><option value="per_tonne">Per tonne</option><option value="per_kg">Per kilogram</option><option value="complete_capacity">Complete available capacity</option><option value="negotiated">Negotiated route amount</option></select></label>
      <button disabled={busy}>{busy?'Publishing…':'Publish route'}</button>
    </form>}
  </details>
}
