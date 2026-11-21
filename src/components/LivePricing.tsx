import {useState} from 'react'
import {Calculator, Clock3, IndianRupee, MapPin, Moon, PackageOpen, Route, Truck} from 'lucide-react'
import {publicFetch} from '../lib/api'
import AddressSearchField from './AddressSearchField'
import LocationMap from './LocationMap'
import type {MapPoint} from '../lib/demand-location'
import './LivePricing.css'

type Estimate={distance_km:string;duration_minutes:number;route_source:string;suggested_low:string;suggested_high:string;breakdown:Record<string,string>;message:string}
const money=(value:string)=>`₹${Number(value).toLocaleString('en-IN',{maximumFractionDigits:2})}`
const labels:Record<string,string>={base_trip:'Base trip',loading:'Loading assistance',unloading:'Unloading assistance',extra_stops:'Stops beyond two',night:'Night service',waiting:'Waiting after first hour'}

export default function LivePricing(){
  const [form,setForm]=useState({pickup:'',destination:'',distance:'',vehicles:'1',stops:'0',parcels:'10',waiting:'0',loading:false,unloading:false,night:false})
  const [estimate,setEstimate]=useState<Estimate|null>(null)
  const [message,setMessage]=useState('')
  const [busy,setBusy]=useState(false)
  const [pins,setPins]=useState<{pickup:MapPoint|null;destination:MapPoint|null}>({pickup:null,destination:null})
  const set=(key:keyof typeof form,value:string|boolean)=>setForm(current=>({...current,[key]:value}))
  async function calculate(event:React.FormEvent){
    event.preventDefault();setBusy(true);setMessage('Calculating advisory range…')
    try{
      const result=await publicFetch<Estimate>('/pricing/suggest',{method:'POST',body:JSON.stringify({pickup:form.pickup,destination:form.destination,...(form.distance?{distance_km:Number(form.distance)}:{}),vehicle_count:Number(form.vehicles),stops:Array.from({length:Number(form.stops)},(_,index)=>`Stop ${index+1}`),loading:form.loading,unloading:form.unloading,package_count:Number(form.parcels),night_trip:form.night,expected_waiting_hours:Number(form.waiting)})})
      setEstimate(result);setMessage('')
    }catch(error){setEstimate(null);setMessage(error instanceof Error?error.message:'Suggestion unavailable')}
    finally{setBusy(false)}
  }
  return <main className="page"><div className="page-title"><span className="kicker">ADVISORY PRICING</span><h1>Trip price suggestion</h1><p>Understand the estimated trip and service charges before providers submit their own final quotations.</p></div>
    <div className="advisory-note"><IndianRupee/><div><b>TransivoX does not set the transport price</b><small>This calculator is guidance only. Every transporter chooses their final all-inclusive quotation.</small></div></div>
    <div className="pricing-grid"><form className="panel pricing-form" onSubmit={calculate}><h3><Calculator/> Calculate an estimate</h3><div className="pricing-route"><AddressSearchField id="pricing-pickup" label="Pickup" value={form.pickup} required minLength={2} placeholder="Start typing, then pick from the list" onType={text=>{set('pickup',text);setPins(current=>({...current,pickup:null}))}} onPick={place=>{set('pickup',place.address);setPins(current=>({...current,pickup:{lat:place.lat,lng:place.lng}}))}}/><AddressSearchField id="pricing-destination" label="Destination" value={form.destination} required minLength={2} placeholder="Start typing, then pick from the list" onType={text=>{set('destination',text);setPins(current=>({...current,destination:null}))}} onPick={place=>{set('destination',place.address);setPins(current=>({...current,destination:{lat:place.lat,lng:place.lng}}))}}/></div><LocationMap points={pins}/><label><Route/> Road distance in kilometres — optional, leave blank to calculate it with Google Maps<input type="number" min="1" max="10000" step="0.1" value={form.distance} onChange={e=>set('distance',e.target.value)}/><small>Pick both places from the suggestions and leave this blank to use the Google Maps road distance.</small></label><div className="pricing-numbers"><label><Truck/> Vehicles<input required type="number" min="1" max="100" value={form.vehicles} onChange={e=>set('vehicles',e.target.value)}/></label><label><MapPin/> Intermediate stops<input required type="number" min="0" max="10" value={form.stops} onChange={e=>set('stops',e.target.value)}/></label><label><PackageOpen/> Parcels<input required type="number" min="1" max="100000" value={form.parcels} onChange={e=>set('parcels',e.target.value)}/></label><label><Clock3/> Waiting hours<input required type="number" min="0" max="48" step="0.5" value={form.waiting} onChange={e=>set('waiting',e.target.value)}/></label></div><div className="pricing-options"><label><input type="checkbox" checked={form.loading} onChange={e=>set('loading',e.target.checked)}/> Loading assistance</label><label><input type="checkbox" checked={form.unloading} onChange={e=>set('unloading',e.target.checked)}/> Unloading assistance</label><label><input type="checkbox" checked={form.night} onChange={e=>set('night',e.target.checked)}/><Moon/> Night trip</label></div><button disabled={busy}>{busy?'Calculating…':'Calculate advisory range'}</button>{message&&<div className="form-error">{message}</div>}</form>
      <section className="panel pricing-result">{estimate?<><span className="estimate-label">SUGGESTED RANGE</span><h2>{money(estimate.suggested_low)}–{money(estimate.suggested_high)}</h2><p>{estimate.distance_km} km · approximately {Math.floor(estimate.duration_minutes/60)}h {estimate.duration_minutes%60}m {estimate.route_source==='google_routes'?'using Google Maps road distance':'using the distance you entered'}</p><div className="charge-list">{Object.entries(estimate.breakdown).map(([key,value])=><span className={Number(value)>0?'charged':''} key={key}><small>{labels[key]||key.replaceAll('_',' ')}</small><b>{money(value)}</b></span>)}</div><div className="rules-summary"><span>Loading <b>₹100 + ₹7/parcel</b></span><span>Unloading <b>₹100 + ₹7/parcel</b></span><span>First 2 stops <b>included</b></span><span>Extra stops <b>₹500 each</b></span><span>Night service <b>₹500</b></span><span>First waiting hour <b>included</b></span><span>Additional waiting <b>₹500/hour</b></span></div></>:<div className="pricing-empty"><Calculator/><b>Your breakdown will appear here</b><p>Enter the trip details to separate transport, handling, stops, night service, and waiting charges.</p></div>}</section></div>
  </main>
}
