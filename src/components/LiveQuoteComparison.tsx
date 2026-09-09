import {useEffect, useMemo, useState} from 'react'
import {ArrowRight, BadgeCheck, Check, Star} from 'lucide-react'
import {ApiError, apiFetch, type BookingResult, type MarketplaceRequest, type Quote} from '../lib/api'

function money(value:string){return `₹${Number(value).toLocaleString('en-IN')}`}

export default function LiveQuoteComparison(){
  const [requests,setRequests]=useState<MarketplaceRequest[]>([])
  const [selectedId,setSelectedId]=useState('')
  const [quotes,setQuotes]=useState<Quote[]>([])
  const [allocations,setAllocations]=useState<Record<string,number>>({})
  const [counterId,setCounterId]=useState<string|null>(null)
  const [counterAmount,setCounterAmount]=useState('')
  const [message,setMessage]=useState('')
  const [state,setState]=useState<'loading'|'ready'|'signed-out'|'error'>('loading')
  const [booking,setBooking]=useState<BookingResult|null>(null)

  useEffect(()=>{
    apiFetch<MarketplaceRequest[]>('/requests/mine').then(items=>{
      setRequests(items)
      const first=items.find(item=>item.status==='published')?.id||items[0]?.id||''
      setSelectedId(first);setState('ready')
    }).catch(error=>setState(error instanceof ApiError&&error.status===401?'signed-out':'error'))
  },[])

  useEffect(()=>{
    if(!selectedId){setQuotes([]);return}
    setMessage('Loading quotations…')
    apiFetch<Quote[]>(`/requests/${selectedId}/quotes`).then(items=>{
      setQuotes(items);setAllocations({});setBooking(null);setMessage('')
    }).catch(error=>setMessage(error instanceof Error?error.message:'Unable to load quotations'))
  },[selectedId])

  const selected=useMemo(()=>requests.find(item=>item.id===selectedId),[requests,selectedId])
  const allocated=Object.values(allocations).reduce((total,count)=>total+count,0)
  const required=selected?.vehicle_count||0
  const total=quotes.reduce((sum,quote)=>sum+(allocations[quote.id]||0)*Number(quote.final_price)/quote.vehicles_offered,0)

  function update(quote:Quote,next:number){
    if(quote.service_mode==='SHARED_CAPACITY')return
    const other=allocated-(allocations[quote.id]||0)
    setAllocations({...allocations,[quote.id]:Math.max(0,Math.min(next,quote.vehicles_offered,required-other))})
  }

  async function sendCounter(quote:Quote){
    try{
      await apiFetch(`/quotes/${quote.id}/counter-offers`,{method:'POST',body:JSON.stringify({sender_role:'customer',amount:Number(counterAmount),message:'Customer counter offer'})})
      setMessage('Counter offer sent.');setCounterId(null)
    }catch(error){setMessage(error instanceof Error?error.message:'Counter offer failed')}
  }

  async function createBooking(){
    if(!selected||allocated!==required)return
    setMessage('Creating booking…')
    try{
      const result=await apiFetch<BookingResult>(`/requests/${selected.id}/bookings`,{method:'POST',body:JSON.stringify({allocations:Object.entries(allocations).filter(([,trucks])=>trucks>0).map(([quote_id,trucks])=>({quote_id,trucks}))})})
      setBooking(result);setMessage('')
    }catch(error){setMessage(error instanceof ApiError?error.message:'Unable to create booking')}
  }

  if(state==='signed-out')return <main className="page"><div className="page-title"><span className="kicker">TRANSIVOX MARKETPLACE</span><h1>Compare quotations</h1><p>Sign in as a customer to view quotations for your requirements.</p></div><div className="empty-state"><b>Sign in required</b><p>Your quotations are private and visible only to your account.</p></div></main>
  if(state==='loading')return <main className="page"><div className="empty-state">Loading your requirements…</div></main>
  if(state==='error')return <main className="page"><div className="empty-state"><b>Unable to load requirements</b><p>Please refresh and try again.</p></div></main>
  if(!requests.length)return <main className="page"><div className="page-title"><span className="kicker">TRANSIVOX MARKETPLACE</span><h1>Compare quotations</h1><p>Quotations appear after you publish a transport requirement.</p></div><div className="empty-state"><b>No requirements yet</b><p>Post your first transport need to receive provider quotations.</p></div></main>
  if(booking)return <main className="page"><div className="page-title"><span className="kicker">TRANSIVOX MARKETPLACE</span><h1>Booking created</h1><p>Your selected quotation and route details have been saved.</p></div><div className="booking-created"><span><Check/></span><div><b>{booking.public_id}</b><p>{booking.trucks_allocated} truck(s) allocated · {money(booking.total_amount)}</p><small>Payment remains pending until a configured payment method is used.</small></div></div></main>

  return <main className="page"><div className="page-title"><span className="kicker">TRANSIVOX MARKETPLACE</span><h1>Compare final quotations</h1><p>Select one of your requirements and allocate the required trucks.</p></div>
    <div className="filterbar"><select value={selectedId} onChange={event=>setSelectedId(event.target.value)}>{requests.map(item=><option value={item.id} key={item.id}>{item.public_id} · {item.pickup_address} to {item.destination_address} · {item.status}</option>)}</select></div>
    <div className="quote-summary"><span><b>{quotes.length}</b><small>quotes received</small></span><span><b>{quotes.length?money(String(Math.min(...quotes.map(q=>Number(q.final_price))))):'—'}</b><small>lowest final price</small></span><span><b>{allocated} / {required}</b><small>trucks allocated</small></span><button disabled={allocated!==required||!quotes.length} onClick={createBooking}>Confirm allocation</button></div>
    {message&&<div className="privacy-banner">{message}</div>}
    {!quotes.length&&!message?<div className="empty-state"><b>No active quotations</b><p>Verified providers can quote after the request is published.</p></div>:<div className="comparison-list">{quotes.map((quote,index)=><article className={`comparison-card ${index===0?'best':''} ${allocations[quote.id]?'selected-quote':''}`} key={quote.id}>{index===0&&<div className="best-ribbon">LOWEST PRICE</div>}<div className="provider-cell"><span className="provider-avatar">{quote.provider_name.split(' ').map(x=>x[0]).join('').slice(0,2)}</span><div><h3>{quote.provider_name} {quote.verified&&<BadgeCheck/>}</h3><p><Star/> {quote.rating} · {quote.completed_trips} completed trips · {quote.cancellation_percent}% cancellation</p></div></div><div className="comparison-facts"><span><small>FINAL PRICE</small><b>{money(quote.final_price)}</b></span><span><small>VEHICLE</small><b>{quote.vehicles_offered} × {quote.vehicle_name}</b></span><span><small>SERVICE</small><b>{quote.service_mode.replaceAll('_',' ')}</b></span></div><div className="comparison-actions"><button className="secondary-action" onClick={()=>{setCounterId(quote.id);setCounterAmount(quote.final_price)}}>Counter offer</button>{quote.service_mode==='SHARED_CAPACITY'?<small>Reserve shared capacity first</small>:<label className="allocation-stepper"><small>ALLOCATE</small><span><button onClick={()=>update(quote,(allocations[quote.id]||0)-1)}>−</button><b>{allocations[quote.id]||0}</b><button onClick={()=>update(quote,(allocations[quote.id]||0)+1)}>+</button></span></label>}</div>{counterId===quote.id&&<div className="counter-box"><label>Your offer<input inputMode="decimal" value={counterAmount} onChange={event=>setCounterAmount(event.target.value)}/></label><button disabled={!Number(counterAmount)} onClick={()=>sendCounter(quote)}>Send offer <ArrowRight/></button></div>}</article>)}</div>}
    {allocated>0&&<div className="price-callout"><span>Selected quotation total</span><b>{money(String(total))}</b></div>}
  </main>
}
