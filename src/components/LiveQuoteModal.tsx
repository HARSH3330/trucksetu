import {useEffect, useState} from 'react'
import {ArrowRight, Check, X} from 'lucide-react'
import {ApiError, apiFetch, publicFetch, type ProviderProfile, type Quote, type VehicleCategory} from '../lib/api'

type Load = {id:string;requestId?:string;from:string;to:string;trucks:number;budget:string}

export default function LiveQuoteModal({load,close}:{load:Load;close:()=>void}){
  const [profile,setProfile]=useState<ProviderProfile|null>(null)
  const [categories,setCategories]=useState<VehicleCategory[]>([])
  const [price,setPrice]=useState('')
  const [vehicles,setVehicles]=useState(String(load.trucks))
  const [categoryId,setCategoryId]=useState('')
  const [pickup,setPickup]=useState('')
  const [delivery,setDelivery]=useState('')
  const [notes,setNotes]=useState('Includes tolls and driver expenses.')
  const [state,setState]=useState<'loading'|'ready'|'signed-out'|'error'|'sent'>('loading')
  const [message,setMessage]=useState('')

  useEffect(()=>{
    Promise.all([apiFetch<ProviderProfile>('/providers/me'),publicFetch<VehicleCategory[]>('/vehicle-categories')])
      .then(([provider,items])=>{setProfile(provider);setCategories(items);setCategoryId(items[0]?.id||'');setState('ready')})
      .catch(error=>{setMessage(error instanceof Error?error.message:'Unable to prepare quotation');setState(error instanceof ApiError&&error.status===401?'signed-out':'error')})
  },[])

  async function submit(event:React.FormEvent){
    event.preventDefault()
    if(!load.requestId||!profile)return
    setMessage('Submitting quotation…')
    try{
      await apiFetch<Quote>(`/requests/${load.requestId}/quotes`,{method:'POST',body:JSON.stringify({
        provider_id:profile.id,vehicle_category_id:categoryId,service_mode:'FULL_VEHICLE',
        final_price:Number(price),vehicles_offered:Number(vehicles),
        estimated_pickup:new Date(pickup).toISOString(),estimated_delivery:new Date(delivery).toISOString(),notes,
      })})
      setState('sent');setMessage('')
    }catch(error){setMessage(error instanceof Error?error.message:'Quotation could not be submitted')}
  }

  if(state==='sent')return <div className="overlay"><div className="modal success"><span><Check/></span><h2>Quotation submitted</h2><p>Your final quote of ₹{Number(price).toLocaleString('en-IN')} is now visible to the customer.</p><button onClick={close}>Back to loads</button></div></div>
  return <div className="overlay"><div className="modal"><button className="modal-close" onClick={close}><X/></button><div className="wizard-head"><small>QUOTE FOR {load.id}</small><h2>{load.from} to {load.to}</h2>{profile&&<p>{profile.display_name} · KYC {profile.kyc_status}</p>}</div>
    {state==='loading'?<div className="empty-state">Loading your provider profile…</div>:state==='signed-out'?<div className="empty-state"><b>Provider sign-in required</b><p>Sign in with your provider or fleet-owner account to quote.</p></div>:state==='error'?<div className="form-error" role="alert">{message}</div>:<form onSubmit={submit}><div className="quote-market"><span><small>Customer budget</small><b>{load.budget}</b></span><span><small>Vehicles required</small><b>{load.trucks}</b></span><p>Only a verified, active provider can submit a quotation.</p></div><div className="fields"><label>Final all-inclusive price<input required min="1" type="number" inputMode="decimal" value={price} onChange={event=>setPrice(event.target.value)}/></label><div className="row"><label>Vehicles offered<input required type="number" value={vehicles} onChange={event=>setVehicles(event.target.value)} min="1" max={load.trucks}/></label><label>Vehicle category<select required value={categoryId} onChange={event=>setCategoryId(event.target.value)}>{categories.map(item=><option value={item.id} key={item.id}>{item.name} · up to {item.max_capacity_tonnes} t</option>)}</select></label></div><div className="row"><label>Estimated pickup<input required type="datetime-local" value={pickup} onChange={event=>setPickup(event.target.value)}/></label><label>Estimated delivery<input required type="datetime-local" value={delivery} onChange={event=>setDelivery(event.target.value)}/></label></div><label>Quote notes<textarea value={notes} onChange={event=>setNotes(event.target.value)}/></label>{message&&<div className="form-error" role="alert">{message}</div>}<div className="price-callout"><span>Customer sees one clear amount</span><b>FINAL PRICE ₹{Number(price||0).toLocaleString('en-IN')}</b></div></div><div className="wizard-foot"><button type="button" className="secondary" onClick={close}>Cancel</button><button disabled={!categoryId||!price||!pickup||!delivery||Number(vehicles)<1}>Submit quotation <ArrowRight/></button></div></form>}
  </div></div>
}
