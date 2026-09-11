import {useEffect, useState} from 'react'
import {BadgeCheck, Building2, FileCheck2, FilePlus2, ReceiptIndianRupee} from 'lucide-react'
import {ApiError, apiFetch, type CurrentUser} from '../lib/api'
import './LiveInvoices.css'

type Booking={booking_id:string;booking_public_id:string;total_amount:string;due_amount:string;can_report_payment:boolean}
type Invoice={id:string;booking_id:string;booking_public_id:string;invoice_number:string;legal_name:string;gstin:string|null;billing_address:string;taxable_amount:string;tax_percent:string;tax_amount:string;total_amount:string;status:string;issued_at:string|null}
const money=(value:string)=>`₹${Number(value).toLocaleString('en-IN',{minimumFractionDigits:2,maximumFractionDigits:2})}`

export default function LiveInvoices(){
  const [user,setUser]=useState<CurrentUser|null>(null)
  const [bookings,setBookings]=useState<Booking[]>([])
  const [invoices,setInvoices]=useState<Invoice[]>([])
  const [state,setState]=useState<'loading'|'ready'|'signed-out'|'error'>('loading')
  const [bookingId,setBookingId]=useState('')
  const [legalName,setLegalName]=useState('')
  const [gstin,setGstin]=useState('')
  const [address,setAddress]=useState('')
  const [message,setMessage]=useState('')

  async function load(){
    setState('loading')
    try{
      const [account,bookingRows,invoiceRows]=await Promise.all([apiFetch<CurrentUser>('/auth/me'),apiFetch<Booking[]>('/payments'),apiFetch<Invoice[]>('/invoices')])
      setUser(account);setBookings(bookingRows);setInvoices(invoiceRows)
      const invoiced=new Set(invoiceRows.map(item=>item.booking_id))
      setBookingId(current=>current&&!invoiced.has(current)?current:bookingRows.find(item=>item.can_report_payment&&!invoiced.has(item.booking_id))?.booking_id||'')
      setState('ready')
    }catch(error){setState(error instanceof ApiError&&error.status===401?'signed-out':'error');setMessage(error instanceof Error?error.message:'Invoices unavailable')}
  }
  useEffect(()=>{void load()},[])

  async function create(event:React.FormEvent){
    event.preventDefault();setMessage('Creating invoice draft…')
    try{
      await apiFetch(`/bookings/${bookingId}/invoice`,{method:'POST',body:JSON.stringify({legal_name:legalName,gstin:gstin||null,billing_address:address})})
      setLegalName('');setGstin('');setAddress('');setMessage('Invoice draft created for administrator review.');await load()
    }catch(error){setMessage(error instanceof Error?error.message:'Invoice could not be created')}
  }
  async function issue(id:string){
    setMessage('Issuing invoice…')
    try{await apiFetch(`/invoices/${id}/issue`,{method:'POST'});setMessage('Invoice issued and audit logged.');await load()}
    catch(error){setMessage(error instanceof Error?error.message:'Invoice could not be issued')}
  }

  if(state==='loading')return <main className="page"><div className="empty-state">Loading invoices…</div></main>
  if(state==='signed-out')return <main className="page"><div className="empty-state"><b>Sign in required</b><p>Invoice details are private.</p></div></main>
  if(state==='error')return <main className="page"><div className="empty-state"><b>Invoices unavailable</b><p>{message}</p><button onClick={load}>Retry</button></div></main>
  const admin=Boolean(user?.roles.some(role=>['admin','superadmin'].includes(role)))
  const available=bookings.filter(item=>item.can_report_payment&&!invoices.some(invoice=>invoice.booking_id===item.booking_id))
  return <main className="page"><div className="page-title"><span className="kicker">FINANCIAL RECORDS</span><h1>Booking invoices</h1><p>Create GST-ready invoice records and track administrator issuance.</p></div>
    {message&&<div className="privacy-banner">{message}</div>}
    <div className="invoice-grid"><section className="invoice-list">{invoices.map(item=><article key={item.id}><div className="invoice-head"><span><ReceiptIndianRupee/></span><div><b>{item.invoice_number}</b><small>{item.booking_public_id} · {item.legal_name}</small></div><strong className={item.status==='issued'?'issued':'draft'}>{item.status==='issued'?<FileCheck2/>:<FilePlus2/>}{item.status}</strong></div><div className="invoice-values"><span><small>Booking value</small><b>{money(item.taxable_amount)}</b></span><span><small>GST ({Number(item.tax_percent)}%)</small><b>{money(item.tax_amount)}</b></span><span><small>Invoice total</small><b>{money(item.total_amount)}</b></span></div><div className="invoice-address"><Building2/><span><b>{item.gstin||'GSTIN not supplied'}</b><small>{item.billing_address}</small></span></div>{item.issued_at&&<small>Issued {new Date(item.issued_at).toLocaleString('en-IN')}</small>}{admin&&item.status==='draft'&&<button onClick={()=>issue(item.id)}><BadgeCheck/> Review and issue</button>}</article>)}{!invoices.length&&<div className="empty-state"><b>No invoices yet</b><p>Create one from an existing booking.</p></div>}</section>
      {!admin&&available.length>0&&<form className="panel invoice-form" onSubmit={create}><h3><FilePlus2/> Create invoice draft</h3><p>Check legal and billing details carefully. Issued invoices cannot be edited here.</p><label>Booking<select required value={bookingId} onChange={e=>setBookingId(e.target.value)}>{available.map(item=><option key={item.booking_id} value={item.booking_id}>{item.booking_public_id} · {money(item.total_amount)}</option>)}</select></label><label>Legal or business name<input required minLength={2} maxLength={200} value={legalName} onChange={e=>setLegalName(e.target.value)}/></label><label>GSTIN (optional)<input pattern="[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z][1-9A-Z]Z[0-9A-Z]" maxLength={15} value={gstin} onChange={e=>setGstin(e.target.value.toUpperCase())}/></label><label>Billing address<textarea required minLength={10} maxLength={1000} value={address} onChange={e=>setAddress(e.target.value)}/></label><button><ReceiptIndianRupee/> Create draft</button></form>}</div>
  </main>
}
