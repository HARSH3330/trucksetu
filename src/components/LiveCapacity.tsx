import {useEffect,useState} from 'react'
import {ArrowRightIcon as ArrowRight, SealCheckIcon as BadgeCheck, ClockIcon as Clock3, MapPinIcon as MapPin, PathIcon as Route, MagnifyingGlassIcon as Search, StarIcon as Star, TruckIcon as Truck} from '@phosphor-icons/react'
import {publicFetch, type AvailableRoute, type CurrentUser} from '../lib/api'
import CapacityPublication from './CapacityPublication'
import SharedCapacityRequest from './SharedCapacityRequest'
import SharedProviderQuotes from './SharedProviderQuotes'
import SharedQuoteRevisions from './SharedQuoteRevisions'
import './LiveCapacity.css'

function price(route:AvailableRoute){
  const amount=`₹${Number(route.price_amount).toLocaleString('en-IN')}`
  return route.price_basis==='per_tonne'?`${amount} / tonne`:route.price_basis==='per_kg'?`${amount} / kg`:amount
}

export default function LiveCapacity({user}:{user:CurrentUser|null}){
  const [origin,setOrigin]=useState('')
  const [destination,setDestination]=useState('')
  const [cargo,setCargo]=useState('')
  const [tonnes,setTonnes]=useState('')
  const [items,setItems]=useState<AvailableRoute[]>([])
  const [state,setState]=useState<'idle'|'loading'|'ready'|'error'>('idle')
  const [message,setMessage]=useState('')
  const [publicationAvailable,setPublicationAvailable]=useState<boolean|null>(null)
  useEffect(()=>{let current=true;publicFetch<{provider_first_publication_available:boolean}>('/marketplace').then(config=>{if(current)setPublicationAvailable(config.provider_first_publication_available===true)}).catch(()=>{if(current)setPublicationAvailable(false)});return()=>{current=false}},[])

  async function search(event:React.FormEvent){
    event.preventDefault();setState('loading');setMessage('')
    const query=new URLSearchParams({origin,destination})
    if(cargo.trim())query.set('cargo_type',cargo.trim())
    if(Number(tonnes)>0)query.set('minimum_tonnes',tonnes)
    try{setItems(await publicFetch<AvailableRoute[]>(`/available-routes?${query}`));setState('ready')}
    catch(error){setMessage(error instanceof Error?error.message:'Capacity search is unavailable');setState('error')}
  }

  return <main className="page"><div className="page-title"><span className="kicker">SHARED CAPACITY</span><h1>Trucks already going your way</h1><p>Search provider routes with available shared space.</p></div>
    {user?.roles.some(role=>['provider','fleet_owner'].includes(role))&&<>{publicationAvailable===true?<CapacityPublication/>:<p role="status">{publicationAvailable===null?'Checking route publication availability…':'Public route publishing is unavailable in this customer-led marketplace.'}</p>}<SharedProviderQuotes/><SharedQuoteRevisions/></>}
    <form className="capacity-search" onSubmit={search}><label><MapPin/> Origin<input required minLength={2} value={origin} onChange={e=>setOrigin(e.target.value)} placeholder="Delhi"/></label><label><MapPin/> Destination<input required minLength={2} value={destination} onChange={e=>setDestination(e.target.value)} placeholder="Jaipur"/></label><label>Cargo type<input value={cargo} onChange={e=>setCargo(e.target.value)} placeholder="Furniture (optional)"/></label><label>Minimum tonnes<input type="number" min="0.001" step="0.001" value={tonnes} onChange={e=>setTonnes(e.target.value)} placeholder="Optional"/></label><button disabled={state==='loading'}><Search/> {state==='loading'?'Searching…':'Search routes'}</button></form>
    <div className="match-note"><Route/><span><b>How shared truck space works</b><small>Request capacity on a published route, review the provider final quotation and explicitly accept it. A request or quotation does not guarantee space; suitability and capacity are checked before booking.</small></span></div>
    {state==='idle'?<div className="empty-state"><b>Enter your route</b><p>Only active routes departing in the future will appear.</p></div>:state==='error'?<div className="empty-state"><b>Search unavailable</b><p>{message}</p></div>:state==='ready'&&!items.length?<div className="empty-state"><b>No compatible routes found</b><p>Try nearby cities or post a full transport requirement.</p></div>:<div className="capacityUnavailable">{items.map(item=><article className="capacity-card" key={item.id}><div className="truck-visual"><Truck/></div><div className="cap-main"><span className="badge">{item.provider_verified?<><BadgeCheck/> VERIFIED PROVIDER</>:'PROVIDER'}</span><h3>{item.origin} <ArrowRight/> {item.destination}</h3><p><Clock3/> {new Date(item.departure_at).toLocaleString('en-IN')} {item.expected_arrival_at&&`· arrives ${new Date(item.expected_arrival_at).toLocaleString('en-IN')}`}</p><div className="cap-tags"><span>{item.vehicle_name||'Commercial vehicle'}</span><span>{item.remaining_capacity_tonnes} t remaining</span></div><small>By {item.provider_name||'TransivoX provider'} {item.provider_rating&&<>· <Star/> {item.provider_rating}</>}</small></div><div className="cap-price"><small>{item.minimum_booking_tonnes} t minimum</small><b>{price(item)}</b>{user?.roles.includes('customer')?<SharedCapacityRequest route={item}/>:<span className="route-status">Sign in as a customer to request capacity</span>}</div></article>)}</div>}
  </main>
}
