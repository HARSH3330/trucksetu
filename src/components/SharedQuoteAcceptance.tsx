import {useRef,useState} from 'react'
import {apiFetch,type Quote,type BookingResult} from '../lib/api'
import TermsConsent from './TermsConsent'

export default function SharedQuoteAcceptance({quote,onBooked}:{quote:Quote;onBooked:(booking:BookingResult)=>void}){
  const [checked,setChecked]=useState(false),[busy,setBusy]=useState(false),[message,setMessage]=useState(''),[terms,setTerms]=useState(false)
  const key=useRef(crypto.randomUUID())
  const [hold,setHold]=useState<{reservation_id:string;expires_in_minutes:string}|null>(null)
  async function reserve(){
    setBusy(true);setMessage('')
    try{
      const [requests,matches]=await Promise.all([apiFetch<{id:string;available_route_id:string;cargo_category:string;cargo_weight_tonnes:string;cargo_volume_m3:string}[]>('/requests/mine'),apiFetch<{id:string;available_route_id:string}[]>(`/requests/${requestId()}/shared-matches`)])
      const request=requests.find(item=>item.id===requestId()),match=matches.find(item=>item.available_route_id===quote.available_route_id)
      if(!request||!match)throw new Error('A current route suitability review is required before holding space.')
      const result=await apiFetch<{reservation_id:string;expires_in_minutes:string}>(`/available-routes/${quote.available_route_id}/reservations`,{method:'POST',body:JSON.stringify({match_evaluation_id:match.id,cargo_type:request.cargo_category,weight_tonnes:request.cargo_weight_tonnes,volume_m3:request.cargo_volume_m3,idempotency_key:'hold-'+key.current})})
      setHold(result);setMessage(`Temporary hold expires in ${result.expires_in_minutes} minutes. It does not accept this price or create a paid booking.`)
    }catch(error){setMessage(error instanceof Error?error.message:'Hold failed')}
    finally{setBusy(false)}
  }
  function requestId(){return quote.request_id||''}
  async function accept(consented=false){
    if(!checked||busy)return;setBusy(true);setMessage('')
    try{
      if(!consented){const result=await apiFetch<{accepted:boolean}>('/legal/terms/acceptance');if(!result.accepted){setTerms(true);return}}
      onBooked(await apiFetch<BookingResult>(`/quotes/${quote.id}/accept-shared`,{method:'POST',body:JSON.stringify({expected_version:quote.version,idempotency_key:key.current,accept_final_price:true,capacity_reservation_id:hold?.reservation_id})}))
    }catch(error){setMessage(error instanceof Error?error.message:'Acceptance failed; no payment has been confirmed')}
    finally{setBusy(false)}
  }
  const unavailable=!quote.expires_at||new Date(quote.expires_at).getTime()<=Date.now()||!quote.price_breakdown?.length
  return <section aria-label="Shared quotation acceptance"><p>Provider final total: {quote.currency||'INR'} {quote.final_price} · revision {quote.version}</p><ul>{quote.price_breakdown?.map((charge,index)=><li key={index}>{charge.label}: {quote.currency||'INR'} {charge.amount}</li>)}</ul><p>Included: {quote.inclusions||'Not specified'}<br/>Excluded: {quote.exclusions||'Not specified'}<br/>Valid until: {quote.expires_at?new Date(quote.expires_at).toLocaleString():'New quotation required'}</p><p>A quotation alone guarantees neither capacity nor payment. Booking remains unpaid until the existing payment workflow confirms funds.</p><label><input type="checkbox" checked={checked} disabled={busy||unavailable} onChange={event=>setChecked(event.target.checked)}/>I accept this exact quotation revision and final payable total.</label><button disabled={busy||unavailable||Boolean(hold)} onClick={()=>void reserve()}>Hold available capacity temporarily</button><button disabled={busy||unavailable||!checked} onClick={()=>void accept()}>Accept quote and book shared capacity</button>{hold&&<button disabled={busy} onClick={async()=>{setBusy(true);try{await apiFetch(`/capacity-reservations/${hold.reservation_id}/release`,{method:'POST'});setHold(null);setMessage('Hold released; any later booking rechecks availability.')}catch(error){setMessage(error instanceof Error?error.message:'Release failed')}finally{setBusy(false)}}}>Release unbooked hold</button>}{message&&<p role="alert">{message}</p>}{terms&&<TermsConsent onCancel={()=>setTerms(false)} onAccepted={()=>{setTerms(false);void accept(true)}}/>}</section>
}
