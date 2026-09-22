import {useEffect, useState} from 'react'
import {BadgeCheck, Banknote, Check, Clock3, CreditCard, ReceiptText, ShieldCheck} from 'lucide-react'
import {ApiError, apiFetch, type CurrentUser} from '../lib/api'
import './LivePayments.css'

type Payment={id:string;payment_type:string;provider:string;method:string|null;amount:string;status:string;reference:string|null;created_at:string;paid_at:string|null}
type Ledger={booking_id:string;booking_public_id:string;booking_status:string;total_amount:string;currency:string;paid_amount:string;pending_amount:string;due_amount:string;can_report_payment:boolean;payments:Payment[]}
const money=(value:string)=>`₹${Number(value).toLocaleString('en-IN',{minimumFractionDigits:2,maximumFractionDigits:2})}`
type RazorpayOrder={order_id:string;amount_subunits:number;currency:string;key_id:string}
type RazorpayCheckout={open:()=>void;on:(event:string,handler:(response:unknown)=>void)=>void}
type RazorpayConstructor=new(options:Record<string,unknown>)=>RazorpayCheckout

async function loadRazorpay():Promise<RazorpayConstructor>{
  const browser=window as typeof window & {Razorpay?:RazorpayConstructor}
  if(browser.Razorpay)return browser.Razorpay
  await new Promise<void>((resolve,reject)=>{
    const script=document.createElement('script')
    script.src='https://checkout.razorpay.com/v1/checkout.js'
    script.onload=()=>resolve()
    script.onerror=()=>reject(new Error('Razorpay Checkout could not load.'))
    document.head.appendChild(script)
  })
  if(!browser.Razorpay)throw new Error('Razorpay Checkout is unavailable.')
  return browser.Razorpay
}

export default function LivePayments(){
  const [user,setUser]=useState<CurrentUser|null>(null)
  const [items,setItems]=useState<Ledger[]>([])
  const [state,setState]=useState<'loading'|'ready'|'signed-out'|'error'>('loading')
  const [selected,setSelected]=useState('')
  const [type,setType]=useState<'advance'|'balance'>('advance')
  const [method,setMethod]=useState<'direct_upi'|'bank_transfer'|'cash'>('direct_upi')
  const [amount,setAmount]=useState('')
  const [reference,setReference]=useState('')
  const [message,setMessage]=useState('')
  const [onlineBusy,setOnlineBusy]=useState(false)

  async function load(){
    setState('loading')
    try{
      const [account,ledger]=await Promise.all([apiFetch<CurrentUser>('/auth/me'),apiFetch<Ledger[]>('/payments')])
      setUser(account);setItems(ledger);setSelected(current=>current||ledger.find(item=>item.can_report_payment&&Number(item.due_amount)>0)?.booking_id||'');setState('ready')
    }catch(error){setState(error instanceof ApiError&&error.status===401?'signed-out':'error');setMessage(error instanceof Error?error.message:'Payment records unavailable')}
  }
  useEffect(()=>{void load()},[])
  const chosen=items.find(item=>item.booking_id===selected)
  useEffect(()=>{if(chosen)setAmount(chosen.due_amount)},[selected,chosen?.due_amount])

  async function report(event:React.FormEvent){
    event.preventDefault();if(!chosen)return
    setMessage('Recording payment for administrator confirmation…')
    try{
      await apiFetch(`/bookings/${chosen.booking_id}/payments/offline`,{method:'POST',body:JSON.stringify({payment_type:type,method,amount:Number(amount),reference:reference||null,idempotency_key:crypto.randomUUID()})})
      setReference('');setMessage('Payment reported. It will remain pending until an administrator confirms receipt.');await load()
    }catch(error){setMessage(error instanceof Error?error.message:'Payment could not be recorded')}
  }
  async function confirm(paymentId:string){
    setMessage('Confirming receipt…')
    try{await apiFetch(`/payments/${paymentId}/confirm-offline`,{method:'POST'});setMessage('Offline payment confirmed.');await load()}
    catch(error){setMessage(error instanceof Error?error.message:'Confirmation failed')}
  }
  async function testCheckout(item:Ledger){
    if(onlineBusy)return
    setOnlineBusy(true);setMessage('Creating a Razorpay test order…')
    try{
      const paymentType=item.payments.some(payment=>payment.payment_type==='advance'&&payment.status==='paid')?'balance':'advance'
      const order=await apiFetch<RazorpayOrder>(`/bookings/${item.booking_id}/payments/online`,{method:'POST',body:JSON.stringify({payment_type:paymentType,idempotency_key:crypto.randomUUID()})})
      if(!order.key_id.startsWith('rzp_test_'))throw new Error('Checkout stopped: the API did not return a Razorpay test key.')
      if(!order.order_id||order.amount_subunits<=0)throw new Error('The payment order is incomplete.')
      const Razorpay=await loadRazorpay()
      const checkout=new Razorpay({key:order.key_id,amount:order.amount_subunits,currency:order.currency,order_id:order.order_id,name:'TransivoX',description:`Test booking advance · ${item.booking_public_id}`,handler:()=>{setMessage('Test payment submitted. Razorpay webhook confirmation may take a moment; refresh the ledger to check its status.');void load()},modal:{ondismiss:()=>setMessage('Checkout closed. The pending test order can be reopened.')},theme:{color:'#137a57'}})
      checkout.on('payment.failed',()=>setMessage('Test payment failed. No booking payment has been confirmed.'))
      checkout.open()
      setMessage('Complete the simulated payment in Razorpay Checkout.')
    }catch(error){setMessage(error instanceof Error?error.message:'Test checkout could not be opened')}
    finally{setOnlineBusy(false)}
  }

  if(state==='loading')return <main className="page"><div className="empty-state">Loading payment ledger…</div></main>
  if(state==='signed-out')return <main className="page"><div className="empty-state"><b>Sign in required</b><p>Payment records are private.</p></div></main>
  if(state==='error')return <main className="page"><div className="empty-state"><b>Payment ledger unavailable</b><p>{message}</p><button onClick={load}>Retry</button></div></main>
  const admin=Boolean(user?.roles.some(role=>['admin','superadmin'].includes(role)))
  return <main className="page"><div className="page-title"><span className="kicker">SECURE PAYMENT LEDGER</span><h1>Payments & settlements</h1><p>Live balances from confirmed and pending TransivoX payment records.</p></div>
    <div className="payment-safety"><ShieldCheck/><div><b>Razorpay test checkout</b><small>Checkout opens only with a test key. The booking is marked paid only after a verified payment.captured webhook; no card data is stored here.</small></div></div>
    {message&&<div className="privacy-banner">{message}</div>}
    <button type="button" className="payment-refresh" onClick={()=>void load()}>Refresh payment status</button>
    {!items.length?<div className="empty-state"><b>No bookings to pay</b><p>Payment records appear after a quotation is allocated into a booking.</p></div>:<div className="ledger-grid"><section className="ledger-list">{items.map(item=><article key={item.booking_id}><div className="ledger-title"><span><ReceiptText/></span><div><b>{item.booking_public_id}</b><small>{item.booking_status.replaceAll('_',' ')}</small></div><strong>{money(item.total_amount)}</strong></div><div className="ledger-totals"><span><small>Confirmed</small><b>{money(item.paid_amount)}</b></span><span><small>Pending</small><b>{money(item.pending_amount)}</b></span><span><small>Outstanding</small><b>{money(item.due_amount)}</b></span></div>{item.can_report_payment&&Number(item.due_amount)>0&&<button type="button" className="payment-test-button" disabled={onlineBusy} onClick={()=>void testCheckout(item)}><CreditCard/> {onlineBusy?'Preparing…':'Open Razorpay test checkout'}</button>}<div className="payment-history">{item.payments.map(payment=><div key={payment.id}><span className={`payment-status ${payment.status==='paid'?'ok':'pending'}`}>{payment.status==='paid'?<Check/>:<Clock3/>}{payment.status.replaceAll('_',' ')}</span><span><b>{payment.payment_type} · {payment.method||payment.provider}</b><small>{payment.reference||'No reference'} · {new Date(payment.created_at).toLocaleString('en-IN')}</small></span><strong>{money(payment.amount)}</strong>{admin&&payment.provider==='offline'&&payment.status==='pending_confirmation'&&<button onClick={()=>confirm(payment.id)}><BadgeCheck/> Confirm</button>}</div>)}{!item.payments.length&&<small>No payment attempts recorded.</small>}</div></article>)}</section>
      {items.some(item=>item.can_report_payment&&Number(item.due_amount)>0)&&<form className="panel payment-report" onSubmit={report}><h3><Banknote/> Report an offline payment</h3><p>This creates a pending record. It does not mark money as received.</p><label>Booking<select required value={selected} onChange={e=>setSelected(e.target.value)}>{items.filter(item=>item.can_report_payment&&Number(item.due_amount)>0).map(item=><option key={item.booking_id} value={item.booking_id}>{item.booking_public_id} · due {money(item.due_amount)}</option>)}</select></label><label>Payment stage<select value={type} onChange={e=>setType(e.target.value as 'advance'|'balance')}><option value="advance">Booking advance</option><option value="balance">Final balance</option></select></label><label>Method<select value={method} onChange={e=>setMethod(e.target.value as typeof method)}><option value="direct_upi">Direct UPI</option><option value="bank_transfer">Bank transfer</option><option value="cash">Cash</option></select></label><label>Amount<input required type="number" min="0.01" step="0.01" max={chosen?.due_amount} value={amount} onChange={e=>setAmount(e.target.value)}/></label><label>Transaction reference<input maxLength={100} value={reference} onChange={e=>setReference(e.target.value)} placeholder="Optional for cash"/></label><button disabled={!chosen||Number(amount)<=0}><CreditCard/> Submit for confirmation</button></form>}</div>}
  </main>
}
