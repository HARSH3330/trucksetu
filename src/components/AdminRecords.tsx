import {useEffect,useRef,useState} from 'react'
import {apiFetch,ApiError} from '../lib/api'
import './AdminRecords.css'

type User={id:string;name:string;email:string;status:string;roles:string[];email_verified:boolean;mobile?:string|null;mobile_verified?:boolean;customer_kyc_status?:string|null;provider_kyc_status?:string|null}
type RowMode='status'|'verification'
type Booking={id:string;reference:string;customer_name:string;status:string;total_amount:string}
type Requirement={id:string;reference:string;route:string;status:string;pickup_date:string;customer_name:string;bid_count:number;is_test:boolean}
type Page<T>={items:T[];page:number;page_size:number;total:number}
type Tab='users'|'requirements'|'bookings'
const TABS:[Tab,string][]=[['users','Users'],['requirements','Requirements'],['bookings','Bookings']]
const SEARCH_LABEL:Record<Tab,string>={users:'Search name or email',requirements:'Search reference or city',bookings:'Search booking reference'}
const privileged=(item:User)=>item.roles.some(role=>['admin','superadmin'].includes(role))

const words=(value:string)=>value.replaceAll('_',' ')
export function verificationSummary(item:User):string[]{
  const lines=[`Email: ${item.email_verified?'verified':'not verified'}`,item.mobile?`Phone ${item.mobile}: ${item.mobile_verified?'verified':'not verified'}`:'Phone: not added']
  if(item.roles.includes('customer'))lines.push(`PAN: ${item.customer_kyc_status?words(item.customer_kyc_status):'not started'}`)
  if(item.roles.some(role=>['provider','fleet_owner'].includes(role)))lines.push(`Provider verification: ${item.provider_kyc_status?words(item.provider_kyc_status):'not started'}`)
  return lines
}

/** Superadmin-only email/phone override. PAN and provider verification keep their own review flow. */
function VerificationForm({item,onClose,onSaved}:{item:User;onClose:()=>void;onSaved:(message:string)=>void}){
  const choices:{value:string;label:string;channel:'email'|'mobile';verified:boolean}[]=[
    {value:'email',label:`Mark email ${item.email_verified?'not verified':'verified'}`,channel:'email',verified:!item.email_verified},
    ...(item.mobile||item.mobile_verified?[{value:'mobile',label:`Mark phone ${item.mobile_verified?'not verified':'verified'}`,channel:'mobile' as const,verified:!item.mobile_verified}]:[]),
  ]
  const [choice,setChoice]=useState(choices[0].value),[reason,setReason]=useState(''),[saving,setSaving]=useState(false),[error,setError]=useState('')
  const heading=useRef<HTMLHeadingElement>(null)
  useEffect(()=>heading.current?.focus(),[])
  const picked=choices.find(entry=>entry.value===choice)||choices[0]
  async function save(event:React.FormEvent){
    event.preventDefault();if(saving||reason.trim().length<10)return
    setSaving(true);setError('')
    try{await apiFetch(`/admin/users/${item.id}/contact-verification`,{method:'POST',body:JSON.stringify({channel:picked.channel,verified:picked.verified,reason:reason.trim()})});onSaved(`${item.name}: ${picked.channel==='email'?'email':'phone'} is now ${picked.verified?'verified':'not verified'}.`)}
    catch(failure){setError(failure instanceof Error?failure.message:'Verification change failed')}
    finally{setSaving(false)}
  }
  return <form className="admin-status-form" onSubmit={save} onKeyDown={event=>{if(event.key==='Escape'&&!saving)onClose()}}>
    <h3 ref={heading} tabIndex={-1}>Edit verification: {item.name}</h3>
    <label>Change<select value={choice} onChange={event=>setChoice(event.target.value)}>{choices.map(entry=><option key={entry.value} value={entry.value}>{entry.label}</option>)}</select></label>
    {!item.mobile&&<p>No phone number is saved on this account, so phone verification cannot be marked.</p>}
    <p>This changes only email or phone verification. PAN and provider verification stay in the Verification queue.</p>
    <label>Reason (kept in the audit log, at least 10 characters)<textarea required minLength={10} maxLength={2000} value={reason} onChange={event=>setReason(event.target.value)}/></label>
    {error&&<p role="alert" className="form-error">{error}</p>}
    <div className="admin-actions"><button disabled={saving||reason.trim().length<10}>{saving?'Saving…':'Save verification change'}</button><button type="button" className="secondary" disabled={saving} onClick={onClose}>Cancel</button></div>
  </form>
}

/** One account; forms open inside the row so the admin sees them where they clicked. */
export function UserRow({item,open,busy,onOpen,onClose,onSaved,onDriverReview,superadmin=false}:{item:User;open:boolean|RowMode;busy:boolean;onOpen:(mode?:RowMode)=>void;onClose:()=>void;onSaved:(message:string)=>void;onDriverReview?:()=>void;superadmin?:boolean}){
  const statusOpen=open===true||open==='status'
  const [decision,setDecision]=useState<'active'|'suspended'>(item.status==='active'?'suspended':'active'),[reason,setReason]=useState(''),[saving,setSaving]=useState(false),[error,setError]=useState('')
  const heading=useRef<HTMLHeadingElement>(null)
  useEffect(()=>{if(statusOpen){setDecision(item.status==='active'?'suspended':'active');setReason('');setError('');heading.current?.focus()}},[statusOpen,item.status])
  async function save(event:React.FormEvent){
    event.preventDefault();if(saving||reason.trim().length<10)return
    setSaving(true);setError('')
    try{await apiFetch(`/admin/users/${item.id}/status`,{method:'POST',body:JSON.stringify({status:decision,reason:reason.trim()})});onSaved(decision==='suspended'?`${item.name} is suspended and signed out everywhere.`:`${item.name} can sign in again. Truck and driver eligibility needs a separate review.`)}
    catch(failure){setError(failure instanceof Error?failure.message:'Status change failed')}
    finally{setSaving(false)}
  }
  return <article className="admin-record">
    <div><b>{item.name}</b><small>{item.email} · {item.roles.join(', ')} · {item.status}</small><small className="admin-verification-line">{verificationSummary(item).join(' · ')}</small></div>
    {privileged(item)?<small className="admin-note">Admin accounts are managed separately.</small>:<div className="admin-actions">
      {!open&&<button className="secondary" disabled={busy} onClick={()=>onOpen('status')}>Change account status</button>}
      {!open&&superadmin&&<button className="secondary" disabled={busy} onClick={()=>onOpen('verification')}>Edit verification</button>}
      {onDriverReview&&item.roles.includes('driver')&&<button className="secondary" disabled={busy||item.status!=='active'} onClick={onDriverReview}>Review driver reactivation</button>}
    </div>}
    {open==='verification'&&superadmin&&!privileged(item)&&<VerificationForm item={item} onClose={onClose} onSaved={onSaved}/>}
    {statusOpen&&!privileged(item)&&<form className="admin-status-form" onSubmit={save} onKeyDown={event=>{if(event.key==='Escape'&&!saving)onClose()}}>
      <h3 ref={heading} tabIndex={-1}>Change status: {item.name}</h3>
      <label>New status<select value={decision} onChange={event=>setDecision(event.target.value as 'active'|'suspended')}><option value="suspended">Suspend</option><option value="active">Reactivate account only</option></select></label>
      <p>{decision==='suspended'?'They will be signed out everywhere and cannot bid, post or drive until reactivated.':'They can sign in again. Their truck-owner or driver approval stays off until reviewed separately.'}</p>
      <label>Reason (kept in the audit log, at least 10 characters)<textarea required minLength={10} maxLength={2000} value={reason} onChange={event=>setReason(event.target.value)}/></label>
      {error&&<p role="alert" className="form-error">{error}</p>}
      <div className="admin-actions"><button disabled={saving||reason.trim().length<10}>{saving?'Saving…':decision==='suspended'?'Confirm suspension':'Confirm reactivation'}</button><button type="button" className="secondary" disabled={saving} onClick={onClose}>Cancel</button></div>
    </form>}
  </article>
}

export function RequirementRow({item}:{item:Requirement}){
  return <article className="admin-record"><div><b>{item.route} {item.is_test&&<span className="admin-badge">TEST data</span>}</b><small>{item.reference} · {item.status} · pickup {item.pickup_date} · {item.customer_name} · {item.bid_count} {item.bid_count===1?'bid':'bids'}</small></div></article>
}

export default function AdminRecords({superadmin=false}:{superadmin?:boolean}){
  const [tab,setTab]=useState<Tab>('users'),[q,setQ]=useState(''),[search,setSearch]=useState(''),[page,setPage]=useState(1)
  const [data,setData]=useState<Page<User|Booking|Requirement>|null>(null),[state,setState]=useState('loading'),[message,setMessage]=useState('')
  const [selected,setSelected]=useState<{id:string;mode:RowMode}|null>(null),[busy,setBusy]=useState(false)
  const [driverReview,setDriverReview]=useState<User|null>(null),[driverReason,setDriverReason]=useState('')
  async function reactivateDriver(event:React.FormEvent){event.preventDefault();if(!driverReview||busy||driverReason.trim().length<10)return;setBusy(true);try{await apiFetch(`/admin/users/${driverReview.id}/driver-reactivation`,{method:'POST',body:JSON.stringify({reason:driverReason.trim()})});setDriverReview(null);setDriverReason('');setMessage('Driver eligibility restored after server-side identity, licence and scan checks.');await load()}catch(error){setMessage(error instanceof Error?error.message:'Driver review failed')}finally{setBusy(false)}}
  async function load(){setState('loading');try{setData(await apiFetch<Page<User|Booking|Requirement>>(`/admin/${tab}?q=${encodeURIComponent(search)}&page=${page}&page_size=25`));setState('ready')}catch(error){setState(error instanceof ApiError&&[401,403].includes(error.status)?'forbidden':'error')}}
  useEffect(()=>{void load()},[tab,search,page])
  return <section className="panel admin-records"><h2>Operational records</h2><div className="fleet-tabs" role="group" aria-label="Record type">{TABS.map(([value,label])=><button key={value} aria-pressed={tab===value} className={tab===value?'active':undefined} onClick={()=>{setTab(value);setPage(1);setSelected(null);setMessage('')}}>{label}</button>)}</div>
    <form className="admin-search" onSubmit={event=>{event.preventDefault();setSearch(q);setPage(1)}}><label>{SEARCH_LABEL[tab]}<input maxLength={100} value={q} onChange={event=>setQ(event.target.value)}/></label><button>Search</button></form>
    {state==='loading'&&<p role="status">Loading operational records…</p>}{state==='forbidden'&&<p role="alert">Administrator access required.</p>}{state==='error'&&<button onClick={load}>Retry records</button>}{message&&<p role="status">{message}</p>}
    {state==='ready'&&data&&<><div className="admin-record-list">{data.items.map(item=>'roles' in item
      ?<UserRow key={item.id} item={item} superadmin={superadmin} open={selected?.id===item.id?selected.mode:false} busy={busy} onOpen={mode=>{setSelected({id:item.id,mode:mode||'status'});setDriverReview(null);setMessage('')}} onClose={()=>setSelected(null)} onSaved={text=>{setSelected(null);setMessage(text);void load()}} onDriverReview={()=>{setDriverReview(item);setDriverReason('');setSelected(null)}}/>
      :'route' in item?<RequirementRow key={item.id} item={item}/>
      :<article key={item.id} className="admin-record"><div><b>{item.reference}</b><small>{item.customer_name} · {item.status} · ₹{item.total_amount}</small></div></article>)}{!data.items.length&&<p>No matching records.</p>}</div>
      <p>Page {page} · {data.total} matching records</p><div className="admin-actions"><button className="secondary" disabled={page<=1} onClick={()=>setPage(value=>value-1)}>Previous page</button><button className="secondary" disabled={page*data.page_size>=data.total} onClick={()=>setPage(value=>value+1)}>Next page</button></div></>}
    {driverReview&&<form className="fleet-form" onSubmit={reactivateDriver}><h3>Driver reactivation: {driverReview.name}</h3><p>This is separate from account activation. The API requires current accepted, version-pinned, clean-scanned identity documents, a current licence and an active verified transport provider.</p><label>Driver review reason<textarea required disabled={busy} minLength={10} maxLength={2000} value={driverReason} onChange={event=>setDriverReason(event.target.value)}/></label><button disabled={busy||driverReason.trim().length<10}>Confirm driver reactivation</button><button type="button" disabled={busy} onClick={()=>setDriverReview(null)}>Cancel driver review</button></form>}
  </section>
}
