import {useEffect, useMemo, useState} from 'react'
import {AlertTriangle, BadgeCheck, Ban, CalendarClock, Check, FileSearch, ShieldAlert, Truck, X} from 'lucide-react'
import {ApiError, apiFetch} from '../lib/api'
import './LiveVehicleReview.css'

type Vehicle={id:string;provider_name:string|null;vehicle_category_name:string|null;registration_number:string;body_type:string;maximum_payload_tonnes:string;maximum_volume_m3:string;permit_territories:string[];service_areas:string[];status:string;review_reason:string|null;reviewed_at:string|null;document_eligible_today:boolean;document_expiries:Record<string,string>}
const documentLabel:Record<string,string>={rc:'Registration certificate',insurance:'Insurance',fitness:'Fitness certificate',pollution:'Pollution certificate',permit:'Commercial permit'}

export default function LiveVehicleReview(){
  const [items,setItems]=useState<Vehicle[]>([])
  const [filter,setFilter]=useState<'pending'|'approved'|'rejected'|'suspended'|'all'>('pending')
  const [selected,setSelected]=useState<Vehicle|null>(null)
  const [decision,setDecision]=useState<'approved'|'rejected'|'suspended'>('approved')
  const [reason,setReason]=useState('')
  const [state,setState]=useState<'loading'|'ready'|'forbidden'|'error'>('loading')
  const [message,setMessage]=useState('')

  async function load(){
    setState('loading')
    try{setItems(await apiFetch<Vehicle[]>('/carrier-vehicles'));setState('ready')}
    catch(error){setState(error instanceof ApiError&&[401,403].includes(error.status)?'forbidden':'error');setMessage(error instanceof Error?error.message:'Vehicle queue unavailable')}
  }
  useEffect(()=>{void load()},[])
  const visible=useMemo(()=>filter==='all'?items:items.filter(item=>item.status===filter),[items,filter])
  const expired=(item:Vehicle)=>Object.values(item.document_expiries).some(value=>new Date(`${value}T23:59:59`)<new Date())
  function open(item:Vehicle,status:'approved'|'rejected'|'suspended'){
    setSelected(item);setDecision(status)
    setReason(status==='approved'?'Vehicle details and document expiry dates manually reviewed.':'')
  }
  async function submit(){
    if(!selected||reason.trim().length<10)return
    setMessage(`Saving ${decision} decision…`)
    try{await apiFetch(`/admin/carrier-vehicles/${selected.id}/review`,{method:'POST',body:JSON.stringify({status:decision,reason:reason.trim()})});setSelected(null);setReason('');setMessage('Vehicle review saved and audit logged.');await load()}
    catch(error){setMessage(error instanceof Error?error.message:'Review could not be saved')}
  }

  if(state==='loading')return <main className="page"><div className="empty-state">Loading vehicle review queue…</div></main>
  if(state==='forbidden')return <main className="page"><div className="empty-state"><b>Administrator access required</b><p>Fleet approval is restricted to authorised reviewers.</p></div></main>
  if(state==='error')return <main className="page"><div className="empty-state"><b>Review queue unavailable</b><p>{message}</p><button onClick={load}>Retry</button></div></main>
  return <main className="page"><div className="page-title"><span className="kicker">MANUAL COMPLIANCE REVIEW</span><h1>Vehicle approval queue</h1><p>Review declared vehicle specifications and expiry dates before allowing trip assignment.</p></div>
    <div className="review-warning"><ShieldAlert/><div><b>Approval confirms metadata review only</b><small>Document-file inspection remains unavailable until private storage and malware scanning are configured.</small></div></div>
    {message&&<div className="privacy-banner">{message}</div>}
    <div className="review-tabs">{(['pending','approved','rejected','suspended','all'] as const).map(value=><button className={filter===value?'active':''} onClick={()=>setFilter(value)} key={value}>{value} <b>{value==='all'?items.length:items.filter(item=>item.status===value).length}</b></button>)}</div>
    {!visible.length?<div className="empty-state"><b>No {filter} vehicles</b><p>The queue is currently clear.</p></div>:<section className="vehicle-review-list">{visible.map(item=><article key={item.id}><div className="vehicle-review-head"><span><Truck/></span><div><b>{item.registration_number}</b><small>{item.provider_name||'Provider'} · {item.vehicle_category_name||item.body_type}</small></div><strong className={item.status}>{item.status}</strong></div><div className="vehicle-specs"><span><small>PAYLOAD</small><b>{item.maximum_payload_tonnes} t</b></span><span><small>VOLUME</small><b>{item.maximum_volume_m3} m³</b></span><span><small>PERMIT</small><b>{item.permit_territories.join(', ')}</b></span><span><small>SERVICE AREA</small><b>{item.service_areas.join(', ')}</b></span></div><div className="document-dates">{Object.entries(item.document_expiries).map(([key,value])=>{const past=new Date(`${value}T23:59:59`)<new Date();return <span className={past?'expired':''} key={key}><CalendarClock/><small>{documentLabel[key]||key}</small><b>{new Date(value).toLocaleDateString('en-IN')}</b>{past&&<em>EXPIRED</em>}</span>})}</div>{item.review_reason&&<div className="previous-review"><FileSearch/><span><b>Previous review</b><small>{item.review_reason}{item.reviewed_at&&` · ${new Date(item.reviewed_at).toLocaleString('en-IN')}`}</small></span></div>}<div className="review-actions"><button className="approve" disabled={expired(item)} onClick={()=>open(item,'approved')}><BadgeCheck/> Approve</button><button onClick={()=>open(item,'suspended')}><Ban/> Suspend</button><button className="reject" onClick={()=>open(item,'rejected')}><X/> Reject</button>{expired(item)&&<small><AlertTriangle/> Renew expired documents before approval.</small>}</div></article>)}</section>}
    {selected&&<div className="overlay"><div className="modal vehicle-decision"><button className="modal-close" onClick={()=>setSelected(null)}><X/></button><div className="wizard-head"><small>ADMINISTRATOR DECISION</small><h2>{decision} {selected.registration_number}</h2><p>This decision is audit logged and immediately affects trip-assignment eligibility.</p></div><label>Review reason<textarea autoFocus required minLength={10} maxLength={2000} value={reason} onChange={e=>setReason(e.target.value)}/></label><button disabled={reason.trim().length<10} onClick={submit}><Check/> Confirm {decision}</button></div></div>}
  </main>
}
