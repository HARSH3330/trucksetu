import {useEffect, useState} from 'react'
import {AlertTriangle, ArrowRight, BadgeCheck, MapPin, Navigation, ShieldCheck, Truck, UserRoundCheck} from 'lucide-react'
import {ApiError, apiFetch, type CurrentUser, type ProviderProfile} from '../lib/api'
import './LiveTrips.css'

type Trip={id:string;status:string;driver_id:string|null;carrier_vehicle_id:string|null;vehicle_registration:string|null;last_updated_at:string|null}
type Booking={id:string;public_id:string;status:string;pickup:string;destination:string;trips:Trip[]}
type Driver={id:string;full_name:string;kyc_status:string;active:boolean;licence_expires_on:string|null}
type Vehicle={id:string;registration_number:string;vehicle_category_name:string|null;status:string;document_eligible_today:boolean}
const transitions:Record<string,string[]>={driver_assigned:['heading_to_pickup'],heading_to_pickup:['arrived_at_pickup','on_hold'],pickup_verified:['loaded'],loaded:['in_transit'],in_transit:['at_stop','arrived_at_destination','on_hold'],at_stop:['in_transit'],delivery_verified:['delivered'],delivered:['completed'],on_hold:['heading_to_pickup','in_transit']}
const label=(value:string)=>value.replaceAll('_',' ')

export default function LiveTrips(){
  const [user,setUser]=useState<CurrentUser|null>(null)
  const [bookings,setBookings]=useState<Booking[]>([])
  const [drivers,setDrivers]=useState<Driver[]>([])
  const [vehicles,setVehicles]=useState<Vehicle[]>([])
  const [assignments,setAssignments]=useState<Record<string,{driver:string;vehicle:string}>>({})
  const [locations,setLocations]=useState<Record<string,string>>({})
  const [state,setState]=useState<'loading'|'ready'|'signed-out'|'error'>('loading')
  const [message,setMessage]=useState('')

  async function load(){
    setState('loading')
    try{
      const account=await apiFetch<CurrentUser>('/auth/me')
      const bookingRows=await apiFetch<Booking[]>('/bookings')
      setUser(account);setBookings(bookingRows)
      if(account.roles.some(role=>['provider','fleet_owner'].includes(role))){
        const profile=await apiFetch<ProviderProfile>('/providers/me')
        const [driverRows,vehicleRows]=await Promise.all([apiFetch<Driver[]>(`/providers/${profile.id}/drivers`),apiFetch<Vehicle[]>('/carrier-vehicles')])
        setDrivers(driverRows.filter(item=>item.active&&item.kyc_status==='verified'))
        setVehicles(vehicleRows.filter(item=>item.status==='approved'&&item.document_eligible_today))
      }
      setState('ready')
    }catch(error){setState(error instanceof ApiError&&error.status===401?'signed-out':'error');setMessage(error instanceof Error?error.message:'Trip operations unavailable')}
  }
  useEffect(()=>{void load()},[])
  const operator=Boolean(user?.roles.some(role=>['provider','fleet_owner','admin','superadmin'].includes(role)))
  const fleetOperator=Boolean(user?.roles.some(role=>['provider','fleet_owner'].includes(role)))

  async function assign(tripId:string){
    const selection=assignments[tripId]
    if(!selection?.driver||!selection.vehicle)return setMessage('Select both a verified driver and an approved vehicle.')
    setMessage('Assigning driver and vehicle…')
    try{await apiFetch(`/trips/${tripId}/assign-driver`,{method:'POST',body:JSON.stringify({driver_id:selection.driver,carrier_vehicle_id:selection.vehicle})});setMessage('Driver and vehicle assigned.');await load()}
    catch(error){setMessage(error instanceof Error?error.message:'Assignment failed')}
  }
  async function advance(tripId:string,target:string){
    setMessage(`Updating trip to ${label(target)}…`)
    try{await apiFetch(`/trips/${tripId}/status`,{method:'POST',body:JSON.stringify({target,location_text:locations[tripId]||null,notes:null})});setMessage('Trip status updated and audit history recorded.');await load()}
    catch(error){setMessage(error instanceof Error?error.message:'Status update failed')}
  }

  if(state==='loading')return <main className="page"><div className="empty-state">Loading trip operations…</div></main>
  if(state==='signed-out')return <main className="page"><div className="empty-state"><b>Sign in required</b><p>Trip details are private.</p></div></main>
  if(state==='error')return <main className="page"><div className="empty-state"><b>Trip operations unavailable</b><p>{message}</p><button onClick={load}>Retry</button></div></main>
  const trips=bookings.flatMap(booking=>booking.trips.map(trip=>({booking,trip})))
  return <main className="page"><div className="page-title"><span className="kicker">LIVE TRIP CONTROL</span><h1>Trip operations</h1><p>Assign compliant resources and move each truck through the controlled delivery workflow.</p></div>
    <div className="trip-security"><ShieldCheck/><div><b>Pickup and delivery require customer OTP verification</b><small>OTP status transitions cannot be bypassed from this screen. Production SMS delivery stays deferred until MSG91 is configured.</small></div></div>
    {message&&<div className="privacy-banner">{message}</div>}
    {!trips.length?<div className="empty-state"><b>No allocated trips</b><p>Trips appear after a customer accepts a provider quotation.</p></div>:<section className="trip-board">{trips.map(({booking,trip})=>{const next=transitions[trip.status]||[];const assignment=assignments[trip.id]||{driver:'',vehicle:''};return <article key={trip.id}><div className="trip-head"><span><Truck/></span><div><b>{booking.public_id}</b><small>{booking.pickup} <ArrowRight/> {booking.destination}</small></div><strong>{label(trip.status)}</strong></div><div className="trip-progress"><i/><span>{trip.vehicle_registration||'Vehicle not assigned'}</span>{trip.last_updated_at&&<small>Updated {new Date(trip.last_updated_at).toLocaleString('en-IN')}</small>}</div>
      {fleetOperator&&trip.status==='booking_confirmed'&&<div className="assignment-box"><label><UserRoundCheck/> Verified driver<select value={assignment.driver} onChange={e=>setAssignments({...assignments,[trip.id]:{...assignment,driver:e.target.value}})}><option value="">Select driver</option>{drivers.map(item=><option value={item.id} key={item.id}>{item.full_name} · valid to {item.licence_expires_on||'unknown'}</option>)}</select></label><label><BadgeCheck/> Approved vehicle<select value={assignment.vehicle} onChange={e=>setAssignments({...assignments,[trip.id]:{...assignment,vehicle:e.target.value}})}><option value="">Select vehicle</option>{vehicles.map(item=><option value={item.id} key={item.id}>{item.registration_number} · {item.vehicle_category_name||'commercial'}</option>)}</select></label><button disabled={!assignment.driver||!assignment.vehicle} onClick={()=>assign(trip.id)}>Assign resources</button>{(!drivers.length||!vehicles.length)&&<small><AlertTriangle/> An active verified driver and document-eligible approved vehicle are required.</small>}</div>}
      {operator&&next.length>0&&<div className="status-box"><label><MapPin/> Current location (optional)<input maxLength={250} value={locations[trip.id]||''} onChange={e=>setLocations({...locations,[trip.id]:e.target.value})} placeholder="City, landmark or facility"/></label><div>{next.map(target=><button key={target} onClick={()=>advance(trip.id,target)}><Navigation/> Mark {label(target)}</button>)}</div></div>}
      {['arrived_at_pickup','arrived_at_destination'].includes(trip.status)&&<div className="otp-wait"><ShieldCheck/> Waiting for customer {trip.status==='arrived_at_pickup'?'pickup':'delivery'} OTP verification</div>}</article>})}</section>}
  </main>
}
