import {useEffect,useRef,useState} from 'react'
import {apiFetch} from '../lib/api'

type Refund={booking_id:string;booking_public_id:string;approved_amount:string;processed_amount:string;remaining_amount:string}

export default function ManualRefundPanel(){
  const [items,setItems]=useState<Refund[]>([])
  const [selected,setSelected]=useState('')
  const [amount,setAmount]=useState('')
  const [method,setMethod]=useState('bank_transfer')
  const [reference,setReference]=useState('')
  const [confirmed,setConfirmed]=useState(false)
  const [state,setState]=useState<'loading'|'ready'|'error'>('loading')
  const [busy,setBusy]=useState(false)
  const [message,setMessage]=useState('')
  const [page,setPage]=useState(1)
  const key=useRef(crypto.randomUUID())
  async function load(){
    setState('loading')
    try{const rows=await apiFetch<Refund[]>(`/admin/refunds?page=${page}`);setItems(rows);setSelected(rows[0]?.booking_id||'');setAmount(rows[0]?.remaining_amount||'');setState('ready')}
    catch(error){setState('error');setMessage(error instanceof Error?error.message:'Refund queue unavailable')}
  }
  useEffect(()=>{void load()},[page])
  function select(id:string){setSelected(id);setAmount(items.find(item=>item.booking_id===id)?.remaining_amount||'');setReference('');setConfirmed(false);key.current=crypto.randomUUID()}
  async function record(event:React.FormEvent){
    event.preventDefault();if(!confirmed||busy||!selected)return
    setBusy(true);setMessage('')
    try{await apiFetch(`/bookings/${selected}/refunds/manual`,{method:'POST',body:JSON.stringify({amount,method,reference,idempotency_key:key.current})});key.current=crypto.randomUUID();setConfirmed(false);setReference('');setMessage('Completed refund recorded and audit logged. No transfer was initiated.');await load()}
    catch(error){setMessage(error instanceof Error?error.message:'Record could not be confirmed. Retry the same operation; its key is preserved.')}
    finally{setBusy(false)}
  }
  return <section className="panel" role="region" aria-label="Manual refund records"><h2>Manual refund records</h2><p>Record a refund already completed outside TransivoX. This form does not send money.</p>
    {message&&<p role="status">{message}</p>}{state==='loading'?<p>Loading approved refund balances…</p>:state==='error'?<button onClick={()=>void load()}>Retry refund queue</button>:!items.length?<p>No approved refunds awaiting recording.</p>:<form className="fields" onSubmit={record}>
      <label>Refund booking<select disabled={busy} value={selected} onChange={event=>select(event.target.value)}>{items.map(item=><option key={item.booking_id} value={item.booking_id}>{item.booking_public_id} · remaining INR {item.remaining_amount}</option>)}</select></label>
      <label>Refund amount<input required disabled={busy} type="number" min="0.01" step="0.01" max={items.find(item=>item.booking_id===selected)?.remaining_amount} value={amount} onChange={event=>setAmount(event.target.value)}/></label>
      <label>Completed refund method<select disabled={busy} value={method} onChange={event=>setMethod(event.target.value)}><option value="bank_transfer">Bank transfer</option><option value="upi">UPI</option><option value="cash">Cash</option><option value="razorpay">Razorpay refund completed externally</option></select></label>
      <label>Refund reference<input required disabled={busy} minLength={3} maxLength={100} value={reference} onChange={event=>setReference(event.target.value)}/></label>
      <label><input type="checkbox" disabled={busy} checked={confirmed} onChange={event=>setConfirmed(event.target.checked)}/>I confirm this refund was completed outside TransivoX.</label>
      <button disabled={busy||!confirmed||reference.trim().length<3||!amount}>{busy?'Recording…':'Record completed refund'}</button>
    </form>}
    {state==='ready'&&<div><span>Refund page {page}</span><button disabled={busy||page===1} onClick={()=>setPage(value=>value-1)}>Previous refunds</button><button disabled={busy||items.length<100} onClick={()=>setPage(value=>value+1)}>Next refunds</button></div>}
  </section>
}
