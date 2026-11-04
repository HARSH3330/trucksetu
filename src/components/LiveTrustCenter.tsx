import {useEffect, useMemo, useState} from 'react'
import {AlertTriangle, Check, ShieldCheck, Star, X} from 'lucide-react'
import {ApiError, apiFetch} from '../lib/api'
import './LiveTrustCenter.css'

type Target={id:string;name:string;role:'customer'|'provider'}
type Booking={id:string;public_id:string;status:string;total_amount:string;trip_statuses:string[];targets:Target[]}
type Activity={id:string;booking_id:string;created_at:string;status?:string;category?:string;fee?:string;refund?:string;rating?:number}
type Feed={bookings:Booking[];disputes:Activity[];cancellations:Activity[];reviews:Activity[]}
type Preview={booking_status:string;fee_percent:string;fee:string;refund:string}

const empty:Feed={bookings:[],disputes:[],cancellations:[],reviews:[]}
const money=(value:string)=>`₹${Number(value).toLocaleString('en-IN')}`

export default function LiveTrustCenter(){
  const [feed,setFeed]=useState(empty)
  const [state,setState]=useState<'loading'|'ready'|'signed-out'|'error'>('loading')
  const [mode,setMode]=useState<'review'|'dispute'|'cancel'|null>(null)
  const [bookingId,setBookingId]=useState('')
  const [targetId,setTargetId]=useState('')
  const [rating,setRating]=useState(5)
  const [comment,setComment]=useState('')
  const [category,setCategory]=useState('delivery_delay')
  const [description,setDescription]=useState('')
  const [reason,setReason]=useState('plans_changed')
  const [detail,setDetail]=useState('')
  const [preview,setPreview]=useState<Preview|null>(null)
  const [message,setMessage]=useState('')

  function load(){setState('loading');apiFetch<Feed>('/trust/activity').then(data=>{setFeed(data);setBookingId(data.bookings[0]?.id||'');setState('ready')}).catch(error=>setState(error instanceof ApiError&&error.status===401?'signed-out':'error'))}
  useEffect(load,[])
  const booking=useMemo(()=>feed.bookings.find(item=>item.id===bookingId),[feed.bookings,bookingId])
  useEffect(()=>{setTargetId(booking?.targets[0]?.id||'');setPreview(null)},[booking])

  async function openCancel(id:string){setBookingId(id);setMode('cancel');setMessage('Loading cancellation policy…');try{setPreview(await apiFetch<Preview>(`/bookings/${id}/cancellation-preview`));setMessage('')}catch(error){setMessage(error instanceof Error?error.message:'Policy preview unavailable')}}
  function openReview(){const item=feed.bookings.find(x=>x.trip_statuses.length&&x.trip_statuses.every(s=>s==='completed')&&x.targets.length);if(item){setBookingId(item.id);setMode('review')}}
  function openDispute(){const item=feed.bookings[0];if(item){setBookingId(item.id);setMode('dispute')}}
  async function submit(){
    if(!booking)return
    setMessage('Saving…')
    try{
      if(mode==='review')await apiFetch(`/bookings/${booking.id}/reviews`,{method:'POST',body:JSON.stringify({target_id:targetId,target_role:booking.targets.find(x=>x.id===targetId)?.role||'provider',rating,comment:comment||null,tags:[]})})
      if(mode==='dispute')await apiFetch(`/bookings/${booking.id}/disputes`,{method:'POST',body:JSON.stringify({category,description,attachment_keys:[]})})
      if(mode==='cancel')await apiFetch(`/bookings/${booking.id}/cancel`,{method:'POST',body:JSON.stringify({reason_code:reason,reason_detail:detail||null})})
      setMode(null);setMessage('Trust activity updated.');load()
    }catch(error){setMessage(error instanceof Error?error.message:'Unable to complete this action')}
  }

  if(state==='loading')return <main className="page"><div className="empty-state">Loading trust activity…</div></main>
  if(state==='signed-out')return <main className="page"><div className="page-title"><h1>Trust & safety centre</h1></div><div className="empty-state"><b>Sign in required</b><p>Booking support records are private.</p></div></main>
  if(state==='error')return <main className="page"><div className="empty-state"><b>Trust centre unavailable</b><button onClick={load}>Retry</button></div></main>
  return <main className="page"><div className="page-title"><span className="kicker">VERIFIED BOOKING SUPPORT</span><h1>Trust & safety centre</h1><p>Reviews, disputes and cancellations remain attached to their booking.</p></div>{message&&<div className="privacy-banner">{message}</div>}
    <div className="trust-grid"><section className="trust-card"><span className="trust-icon"><Star/></span><h3>Rate a completed trip</h3><p>Only bookings whose every trip is completed can receive a verified review.</p><button disabled={!feed.bookings.some(x=>x.trip_statuses.length&&x.trip_statuses.every(s=>s==='completed')&&x.targets.length)} onClick={openReview}>Write review</button></section><section className="trust-card"><span className="trust-icon"><ShieldCheck/></span><h3>Booking dispute</h3><p>Open a case with a detailed description. Evidence uploads remain disabled until private storage is configured.</p><button disabled={!feed.bookings.length} onClick={openDispute}>Raise dispute</button></section><section className="trust-card"><span className="trust-icon orange"><X/></span><h3>Cancellation policy</h3><p>Preview the stored policy, exact fee and expected refund before confirming.</p><button disabled={!feed.bookings.some(x=>!['completed','cancelled'].includes(x.status))} onClick={()=>{const item=feed.bookings.find(x=>!['completed','cancelled'].includes(x.status));if(item)openCancel(item.id)}}>Review cancellation</button></section></div>
    <section className="panel trust-activity"><div className="panel-head"><h3>Your trust activity</h3><span className="badge">{feed.disputes.length+feed.cancellations.length+feed.reviews.length} RECORDS</span></div>{feed.disputes.map(item=><div className="activity" key={item.id}><span className="activity-icon"><AlertTriangle/></span><div><b>Dispute · {item.category?.replaceAll('_',' ')}</b><small>{feed.bookings.find(x=>x.id===item.booking_id)?.public_id} · {item.status}</small></div></div>)}{feed.cancellations.map(item=><div className="activity" key={item.id}><span className="activity-icon"><X/></span><div><b>Cancellation · refund {money(item.refund||'0')}</b><small>{feed.bookings.find(x=>x.id===item.booking_id)?.public_id} · fee {money(item.fee||'0')}</small></div></div>)}{feed.reviews.map(item=><div className="activity" key={item.id}><span className="activity-icon"><Star/></span><div><b>Verified review · {item.rating}/5</b><small>{feed.bookings.find(x=>x.id===item.booking_id)?.public_id}</small></div></div>)}{!feed.disputes.length&&!feed.cancellations.length&&!feed.reviews.length&&<div className="empty-state">No trust activity yet.</div>}</section>
    {mode&&<div className="overlay"><div className="modal trust-live-modal"><button className="modal-close" onClick={()=>setMode(null)}><X/></button><div className="wizard-head"><small>{mode.toUpperCase()}</small><h2>{mode==='review'?'Submit verified review':mode==='dispute'?'Raise a booking dispute':'Confirm cancellation'}</h2></div><div className="fields"><label>Booking<select value={bookingId} onChange={e=>{setBookingId(e.target.value);if(mode==='cancel')openCancel(e.target.value)}}>{feed.bookings.filter(x=>mode==='review'?x.trip_statuses.length&&x.trip_statuses.every(s=>s==='completed')&&x.targets.length:mode==='cancel'?!['completed','cancelled'].includes(x.status):true).map(x=><option value={x.id} key={x.id}>{x.public_id} · {x.status}</option>)}</select></label>{mode==='review'&&<><label>Rate<select value={targetId} onChange={e=>setTargetId(e.target.value)}>{booking?.targets.map(x=><option value={x.id} key={x.id}>{x.name} · {x.role}</option>)}</select></label><div className="star-input">{[1,2,3,4,5].map(n=><button type="button" className={rating>=n?'active':''} onClick={()=>setRating(n)} key={n}><Star/></button>)}</div><label>Comment<textarea value={comment} onChange={e=>setComment(e.target.value)} maxLength={2000}/></label></>}{mode==='dispute'&&<><label>Category<select value={category} onChange={e=>setCategory(e.target.value)}><option value="delivery_delay">Delivery delay</option><option value="cargo_damage">Cargo damage</option><option value="payment_disagreement">Payment disagreement</option><option value="conduct">Conduct</option></select></label><label>What happened?<textarea required minLength={20} value={description} onChange={e=>setDescription(e.target.value)}/></label></>}{mode==='cancel'&&<><div className="cancel-preview">{preview?<><span><small>POLICY FEE</small><b>{preview.fee_percent}% · {money(preview.fee)}</b></span><span><small>EXPECTED REFUND</small><b>{money(preview.refund)}</b></span></>:message}</div><label>Reason<select value={reason} onChange={e=>setReason(e.target.value)}><option value="plans_changed">Plans changed</option><option value="booked_by_mistake">Booked by mistake</option><option value="provider_requested">Provider requested</option><option value="other">Other</option></select></label><label>Details<textarea value={detail} onChange={e=>setDetail(e.target.value)}/></label></>}</div><button className="trust-action" disabled={(mode==='review'&&!targetId)||(mode==='dispute'&&description.trim().length<20)||(mode==='cancel'&&!preview)} onClick={submit}><Check/> Confirm {mode}</button></div></div>}
  </main>
}
