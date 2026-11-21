import {useEffect,useRef,useState} from 'react'
import {apiFetch,ApiError} from '../lib/api'
import './AdminRecords.css'

type User={id:string;name:string;email:string;status:string;roles:string[];email_verified:boolean;mobile?:string|null;mobile_verified?:boolean;mobile_shared_count?:number;customer_kyc_status?:string|null;provider_kyc_status?:string|null}
type RowMode='status'|'verification'
type Booking={id:string;reference:string;customer_name:string;status:string;total_amount:string;provider_names?:string[];trip_statuses?:string[];driver_assigned?:boolean;open_disputes?:number;connection_fee?:{status:string;payment_status:string;contact_revealed:boolean}|null}
type Requirement={id:string;reference:string;route:string;status:string;pickup_date:string;customer_name:string;bid_count:number;is_test:boolean}
type Dispute={id:string;booking_id:string;booking_reference:string;booking_status:string;category:string;description:string;status:string;priority:string;raised_by_name:string|null;resolution:string|null;resolved_at:string|null;created_at:string;restores_booking_to:string|null}
type Audit={id:string;actor_id:string|null;actor_name:string|null;actor_email:string|null;action:string;entity_type:string;entity_id:string|null;reason:string|null;changes:Record<string,unknown[]>;request_id:string|null;created_at:string}
type Row=User|Booking|Requirement|Dispute|Audit
type Page<T>={items:T[];page:number;page_size:number;total:number}
export type Tab='users'|'requirements'|'bookings'|'disputes'|'audit'
const TABS:[Tab,string][]=[['users','Users'],['requirements','Requirements'],['bookings','Bookings'],['disputes','Disputes'],['audit','Audit log']]
const SEARCH_LABEL:Record<Tab,string>={users:'Search name or email',requirements:'Search reference or city',bookings:'Search booking reference',disputes:'',audit:'Exact action, e.g. dispute.resolved'}
// Server-side filters per tab; values must match the API allowlists.
const FILTERS:Partial<Record<Tab,{param:string;label:string;options:[string,string][]}[]>>={
  users:[{param:'role',label:'Role',options:[['','Any role'],['customer','Customer'],['provider','Provider'],['fleet_owner','Fleet owner'],['driver','Driver'],['admin','Admin'],['superadmin','Superadmin']]},{param:'account_status',label:'Account',options:[['','Any status'],['active','Active'],['suspended','Suspended']]}],
  bookings:[{param:'status',label:'Booking status',options:[['','Any status'],['connection_fee_pending','Connection fee pending'],['advance_pending','Advance pending'],['booking_confirmed','Confirmed'],['disputed','Disputed'],['completed','Completed'],['cancelled','Cancelled']]}],
  disputes:[{param:'status',label:'Dispute status',options:[['open','Open'],['under_review','Under review'],['resolved','Resolved'],['','All']]}],
}
const defaultFilters=(tab:Tab)=>Object.fromEntries((FILTERS[tab]||[]).map(filter=>[filter.param,filter.options[0][0]]))
export function recordsPath(tab:Tab,search:string,filters:Record<string,string>,page:number){
  const params=new URLSearchParams({page:String(page),page_size:'25'})
  if(search&&tab!=='disputes')params.set(tab==='audit'?'action':'q',search)
  for(const [key,value] of Object.entries(filters))if(value)params.set(key,value)
  return `/admin/${tab==='audit'?'audit-logs':tab}?${params}`
}
const privileged=(item:User)=>item.roles.some(role=>['admin','superadmin'].includes(role))

const words=(value:string)=>value.replaceAll('_',' ')
export function verificationSummary(item:User):string[]{
  const lines=[`Email: ${item.email_verified?'verified':'not verified'}`,item.mobile?`Phone ${item.mobile}: ${item.mobile_verified?'verified':'not verified'}`:'Phone: not added']
  const shared=item.mobile_shared_count||0
  if(shared>0)lines.push(`Warning: this phone number is also verified on ${shared} other account${shared===1?'':'s'}`)
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
  const firstUnverified=choices.find(entry=>entry.verified)||choices[0]
  const [choice,setChoice]=useState(firstUnverified.value),[shareConfirmed,setShareConfirmed]=useState(false),[sharedRefused,setSharedRefused]=useState(false),[reason,setReason]=useState(''),[saving,setSaving]=useState(false),[error,setError]=useState('')
  const heading=useRef<HTMLHeadingElement>(null)
  useEffect(()=>heading.current?.focus(),[])
  const picked=choices.find(entry=>entry.value===choice)||choices[0]
  const shared=item.mobile_shared_count||0
  // The server is the source of truth: a 409 also shows the confirmation if the list was out of date.
  const needsShareConfirm=picked.channel==='mobile'&&picked.verified&&(shared>0||sharedRefused)
  async function save(event:React.FormEvent){
    event.preventDefault();if(saving||reason.trim().length<10)return
    setSaving(true);setError('')
    try{await apiFetch(`/admin/users/${item.id}/contact-verification`,{method:'POST',body:JSON.stringify({channel:picked.channel,verified:picked.verified,reason:reason.trim(),...(needsShareConfirm&&shareConfirmed?{allow_shared_number:true}:{})})});onSaved(`${item.name}: ${picked.channel==='email'?'email':'phone'} is now ${picked.verified?'verified':'not verified'}.`)}
    catch(failure){if(failure instanceof ApiError&&failure.status===409&&picked.channel==='mobile'&&/another account/.test(failure.message))setSharedRefused(true);setError(failure instanceof Error?failure.message:'Verification change failed')}
    finally{setSaving(false)}
  }
  return <form className="admin-status-form" onSubmit={save} onKeyDown={event=>{if(event.key==='Escape'&&!saving)onClose()}}>
    <h3 ref={heading} tabIndex={-1}>Edit verification: {item.name}</h3>
    <label>Change<select value={choice} onChange={event=>setChoice(event.target.value)}>{choices.map(entry=><option key={entry.value} value={entry.value}>{entry.label}</option>)}</select></label>
    {needsShareConfirm&&<><p role="alert" className="form-error">{shared>0?`This phone number is also verified on ${shared} other account${shared===1?'':'s'}. `:''}Verify it here only if the same person uses both accounts. The other account keeps its verification.</p><label className="demand-check"><input type="checkbox" required checked={shareConfirmed} onChange={event=>setShareConfirmed(event.target.checked)}/>Verify anyway — the same person uses both accounts</label></>}
    {!item.mobile&&<p>No phone number is saved on this account, so phone verification cannot be marked.</p>}
    <p>This changes only email or phone verification. PAN and provider verification stay in the Verification queue.</p>
    <label>Reason (kept in the audit log, at least 10 characters)<textarea required minLength={10} maxLength={2000} value={reason} onChange={event=>setReason(event.target.value)}/></label>
    {error&&<p role="alert" className="form-error">{error}</p>}
    <div className="admin-actions"><button disabled={saving||reason.trim().length<10||(needsShareConfirm&&!shareConfirmed)}>{saving?'Saving…':'Save verification change'}</button><button type="button" className="secondary" disabled={saving} onClick={onClose}>Cancel</button></div>
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

export function BookingRow({item}:{item:Booking}){
  const trips=item.trip_statuses||[]
  const fee=item.connection_fee
  const disputes=item.open_disputes||0
  return <article className="admin-record"><div><b>{item.reference} {disputes>0&&<span className="admin-badge">{disputes} open dispute{disputes===1?'':'s'}</span>}</b>
    <small>{item.customer_name} · {words(item.status)} · ₹{item.total_amount}</small>
    <small>Truck owner: {item.provider_names?.length?item.provider_names.join(', '):'not allocated'} · {trips.length?`Trips: ${trips.map(words).join(', ')} · ${item.driver_assigned?'driver assigned':'no driver yet'}`:'No trip yet'}</small>
    {fee&&<small>Connection fee: {words(fee.status)} · payment {words(fee.payment_status)} · {fee.contact_revealed?'contact revealed':'contact not revealed'}</small>}
  </div></article>
}

/** Resolving needs a written outcome; the API records it in the audit log and restores the booking when it can. */
export function DisputeRow({item,open,busy,onOpen,onClose,onSaved}:{item:Dispute;open:boolean;busy:boolean;onOpen:()=>void;onClose:()=>void;onSaved:(message:string)=>void}){
  const [resolution,setResolution]=useState(''),[saving,setSaving]=useState(false),[error,setError]=useState('')
  const heading=useRef<HTMLHeadingElement>(null)
  useEffect(()=>{if(open){setResolution('');setError('');heading.current?.focus()}},[open])
  const active=['open','under_review'].includes(item.status)
  async function save(event:React.FormEvent){
    event.preventDefault();if(saving||resolution.trim().length<10)return
    setSaving(true);setError('')
    try{const result=await apiFetch<{booking_status:string|null;note:string|null}>(`/admin/disputes/${item.id}/resolve`,{method:'POST',body:JSON.stringify({resolution:resolution.trim()})});onSaved(`Dispute on ${item.booking_reference} resolved. Booking is now ${words(result.booking_status||'unknown')}.${result.note?' '+result.note:''}`)}
    catch(failure){setError(failure instanceof Error?failure.message:'The dispute could not be resolved')}
    finally{setSaving(false)}
  }
  return <article className="admin-record">
    <div><b>{item.booking_reference} · {words(item.category)} <span className="admin-badge">{words(item.status)}</span></b>
      <small>Raised by {item.raised_by_name||'unknown account'} on {new Date(item.created_at).toLocaleString('en-IN')} · booking {words(item.booking_status)}</small>
      <p className="admin-dispute-text">{item.description}</p>
      {item.resolution&&<small>Resolution: {item.resolution}</small>}
    </div>
    {active&&!open&&<div className="admin-actions"><button className="secondary" disabled={busy} onClick={onOpen}>Resolve dispute</button></div>}
    {active&&open&&<form className="admin-status-form" onSubmit={save} onKeyDown={event=>{if(event.key==='Escape'&&!saving)onClose()}}>
      <h3 ref={heading} tabIndex={-1}>Resolve dispute: {item.booking_reference}</h3>
      <p>{item.restores_booking_to?`If no other dispute is open, the booking goes back to ${words(item.restores_booking_to)}.`:'The booking stays disputed because its earlier status was not recorded; cancel or complete it through the normal flow.'} No money moves and no refund is issued here.</p>
      <label>Resolution (kept in the audit log, at least 10 characters)<textarea required minLength={10} maxLength={2000} value={resolution} onChange={event=>setResolution(event.target.value)}/></label>
      {error&&<p role="alert" className="form-error">{error}</p>}
      <div className="admin-actions"><button disabled={saving||resolution.trim().length<10}>{saving?'Saving…':'Confirm resolution'}</button><button type="button" className="secondary" disabled={saving} onClick={onClose}>Cancel</button></div>
    </form>}
  </article>
}

export function AuditRow({item}:{item:Audit}){
  const changes=Object.entries(item.changes||{}).map(([key,[from,to]])=>`${key}: ${String(from)} → ${String(to)}`)
  return <article className="admin-record"><div><b>{item.action}</b>
    <small>{new Date(item.created_at).toLocaleString('en-IN')} · {item.actor_name?`${item.actor_name}${item.actor_email?` (${item.actor_email})`:''}`:'System'} · {words(item.entity_type)}{item.entity_id?` ${item.entity_id.slice(0,8)}`:''}</small>
    {item.reason&&<small>Reason: {item.reason}</small>}
    {changes.length>0&&<small>{changes.join(' · ')}</small>}
  </div></article>
}

export default function AdminRecords({superadmin=false,initialTab='users'}:{superadmin?:boolean;initialTab?:Tab}){
  const [tab,setTab]=useState<Tab>(initialTab),[q,setQ]=useState(''),[search,setSearch]=useState(''),[page,setPage]=useState(1),[filters,setFilters]=useState<Record<string,string>>(()=>defaultFilters(initialTab))
  const [data,setData]=useState<Page<Row>|null>(null),[state,setState]=useState('loading'),[message,setMessage]=useState('')
  const [selected,setSelected]=useState<{id:string;mode:RowMode}|null>(null),[busy,setBusy]=useState(false)
  const [driverReview,setDriverReview]=useState<User|null>(null),[driverReason,setDriverReason]=useState('')
  async function reactivateDriver(event:React.FormEvent){event.preventDefault();if(!driverReview||busy||driverReason.trim().length<10)return;setBusy(true);try{await apiFetch(`/admin/users/${driverReview.id}/driver-reactivation`,{method:'POST',body:JSON.stringify({reason:driverReason.trim()})});setDriverReview(null);setDriverReason('');setMessage('Driver eligibility restored after server-side identity, licence and scan checks.');await load()}catch(error){setMessage(error instanceof Error?error.message:'Driver review failed')}finally{setBusy(false)}}
  async function load(){setState('loading');try{setData(await apiFetch<Page<Row>>(recordsPath(tab,search,filters,page)));setState('ready')}catch(error){setState(error instanceof ApiError&&[401,403].includes(error.status)?'forbidden':'error')}}
  useEffect(()=>{void load()},[tab,search,page,filters])
  const saved=(text:string)=>{setSelected(null);setMessage(text);void load()}
  return <section className="panel admin-records" id="admin-records"><h2>Operational records</h2><div className="fleet-tabs" role="group" aria-label="Record type">{TABS.map(([value,label])=><button key={value} aria-pressed={tab===value} className={tab===value?'active':undefined} onClick={()=>{setTab(value);setPage(1);setSelected(null);setMessage('');setQ('');setSearch('');setFilters(defaultFilters(value))}}>{label}</button>)}</div>
    <form className="admin-search" onSubmit={event=>{event.preventDefault();setSearch(q);setPage(1)}}>
      {SEARCH_LABEL[tab]&&<label>{SEARCH_LABEL[tab]}<input maxLength={100} value={q} onChange={event=>setQ(event.target.value)}/></label>}
      {(FILTERS[tab]||[]).map(filter=><label key={filter.param}>{filter.label}<select value={filters[filter.param]||''} onChange={event=>{setFilters(current=>({...current,[filter.param]:event.target.value}));setPage(1)}}>{filter.options.map(([value,label])=><option key={value} value={value}>{label}</option>)}</select></label>)}
      {SEARCH_LABEL[tab]&&<button>Search</button>}
    </form>
    {state==='loading'&&<p role="status">Loading operational records…</p>}{state==='forbidden'&&<p role="alert">Administrator access required.</p>}{state==='error'&&<button onClick={load}>Retry records</button>}{message&&<p role="status">{message}</p>}
    {state==='ready'&&data&&<><div className="admin-record-list">{data.items.map(item=>'roles' in item
      ?<UserRow key={item.id} item={item} superadmin={superadmin} open={selected?.id===item.id?selected.mode:false} busy={busy} onOpen={mode=>{setSelected({id:item.id,mode:mode||'status'});setDriverReview(null);setMessage('')}} onClose={()=>setSelected(null)} onSaved={saved} onDriverReview={()=>{setDriverReview(item);setDriverReason('');setSelected(null)}}/>
      :'route' in item?<RequirementRow key={item.id} item={item}/>
      :'description' in item?<DisputeRow key={item.id} item={item} open={selected?.id===item.id} busy={busy} onOpen={()=>{setSelected({id:item.id,mode:'status'});setMessage('')}} onClose={()=>setSelected(null)} onSaved={saved}/>
      :'action' in item?<AuditRow key={item.id} item={item}/>
      :<BookingRow key={item.id} item={item}/>)}{!data.items.length&&<p>No matching records.</p>}</div>
      <p>Page {page} · {data.total} matching records</p><div className="admin-actions"><button className="secondary" disabled={page<=1} onClick={()=>setPage(value=>value-1)}>Previous page</button><button className="secondary" disabled={page*data.page_size>=data.total} onClick={()=>setPage(value=>value+1)}>Next page</button></div></>}
    {driverReview&&<form className="fleet-form" onSubmit={reactivateDriver}><h3>Driver reactivation: {driverReview.name}</h3><p>This is separate from account activation. The API requires current accepted, version-pinned, clean-scanned identity documents, a current licence and an active verified transport provider.</p><label>Driver review reason<textarea required disabled={busy} minLength={10} maxLength={2000} value={driverReason} onChange={event=>setDriverReason(event.target.value)}/></label><button disabled={busy||driverReason.trim().length<10}>Confirm driver reactivation</button><button type="button" disabled={busy} onClick={()=>setDriverReview(null)}>Cancel driver review</button></form>}
  </section>
}
