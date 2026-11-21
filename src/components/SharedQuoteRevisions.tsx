import {useEffect,useState} from 'react'
import {apiFetch,type Quote} from '../lib/api'

function Revision({quote}:{quote:Quote}){
  const [total,setTotal]=useState(quote.final_price),[expiry,setExpiry]=useState(quote.expires_at?new Date(new Date(quote.expires_at).getTime()-new Date().getTimezoneOffset()*60000).toISOString().slice(0,16):'')
  const [charges,setCharges]=useState(quote.price_breakdown||[]),[included,setIncluded]=useState(quote.inclusions||''),[excluded,setExcluded]=useState(quote.exclusions||'')
  const [busy,setBusy]=useState(false),[message,setMessage]=useState('')
  async function submit(event:React.FormEvent){
    event.preventDefault();if(busy)return;setBusy(true);setMessage('')
    try{
      const result=await apiFetch<Quote>(`/quotes/${quote.id}`,{method:'PATCH',body:JSON.stringify({final_price:total,vehicles_offered:1,expires_at:new Date(expiry).toISOString(),price_breakdown:charges,inclusions:included,exclusions:excluded,notes:quote.notes})})
      setMessage(`Revision ${result.version} published. Customer must explicitly accept the new revision.`)
    }catch(error){setMessage(error instanceof Error?error.message:'Revision unavailable')}
    finally{setBusy(false)}
  }
  return <form className="fields" onSubmit={submit}><p>Quotation {quote.id} · loaded revision {quote.version}. The server rejects changes after acceptance. A changed price needs a new suitability review.</p><label>Revised final total (INR)<input required type="number" min="0.01" step="0.01" disabled={busy} value={total} onChange={event=>setTotal(event.target.value)}/></label><label>Revised validity<input required type="datetime-local" disabled={busy} value={expiry} onChange={event=>setExpiry(event.target.value)}/></label><label>Revised included services<input required maxLength={2000} disabled={busy} value={included} onChange={event=>setIncluded(event.target.value)}/></label><label>Revised exclusions<input required maxLength={2000} disabled={busy} value={excluded} onChange={event=>setExcluded(event.target.value)}/></label>{charges.map((charge,index)=><fieldset key={index}><legend>Revised component {index+1}</legend><label>Revised charge name {index+1}<input required minLength={2} maxLength={100} disabled={busy} value={charge.label} onChange={event=>setCharges(charges.map((item,i)=>i===index?{...item,label:event.target.value}:item))}/></label><label>Revised charge amount {index+1}<input required type="number" min="0" step="0.01" disabled={busy} value={charge.amount} onChange={event=>setCharges(charges.map((item,i)=>i===index?{...item,amount:event.target.value}:item))}/></label></fieldset>)}<button type="button" disabled={busy||charges.length>=30} onClick={()=>setCharges([...charges,{label:'',amount:''}])}>Add revised charge</button><button disabled={busy||!charges.length}>Publish new quotation revision</button>{message&&<p role="status">{message}</p>}</form>
}

export default function SharedQuoteRevisions(){
  const [quotes,setQuotes]=useState<Quote[]>([]),[error,setError]=useState(''),[loading,setLoading]=useState(true)
  async function load(){setLoading(true);setError('');try{setQuotes((await apiFetch<Quote[]>('/quotes/mine')).filter(item=>item.service_mode==='SHARED_CAPACITY'&&item.status==='active'))}catch(error){setError(error instanceof Error?error.message:'Quotations unavailable')}finally{setLoading(false)}}
  useEffect(()=>{void load()},[])
  return <details className="panel"><summary>Revise my shared quotations</summary><button onClick={()=>void load()}>Refresh my quotations</button>{loading?<p>Loading quotations…</p>:error?<p role="alert">{error}</p>:quotes.length?quotes.map(quote=><Revision key={`${quote.id}:${quote.version}`} quote={quote}/>):<p>No active shared quotations to revise.</p>}</details>
}
