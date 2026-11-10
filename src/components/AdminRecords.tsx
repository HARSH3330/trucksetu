import {useEffect,useRef,useState} from 'react'
import {apiFetch,ApiError} from '../lib/api'
import './AdminRecords.css'

type User={id:string;name:string;email:string;status:string;roles:string[];email_verified:boolean}
type Booking={id:string;reference:string;customer_name:string;status:string;total_amount:string}
type Requirement={id:string;reference:string;route:string;status:string;pickup_date:string;customer_name:string;bid_count:number;is_test:boolean}
type Page<T>={items:T[];page:number;page_size:number;total:number}
type Tab='users'|'requirements'|'bookings'
const TABS:[Tab,string][]=[['users','Users'],['requirements','Requirements'],['bookings','Bookings']]
const SEARCH_LABEL:Record<Tab,string>={users:'Search name or email',requirements:'Search reference or city',bookings:'Search booking reference'}
const privileged=(item:User)=>item.roles.some(role=>['admin','superadmin'].includes(role))

/** One account; the status form opens inside the row so the admin sees it where they clicked. */
export function UserRow({item,open,busy,onOpen,onClose,onSaved,onDriverReview}:{item:User;open:boolean;busy:boolean;onOpen:()=>void;onClose:()=>void;onSaved:(message:string)=>void;onDriverReview?:()=>void}){
  const [decision,setDecision]=useState<'active'|'suspended'>(item.status==='active'?'suspended':'active'),[reason,setReason]=useState(''),[saving,setSaving]=useState(false),[error,setError]=useState('')
  const heading=useRef<HTMLHeadingElement>(null)
  useEffect(()=>{if(open){setDecision(item.status==='active'?'suspended':'active');setReason('');setError('');heading.current?.focus()}},[open,item.status])
  async function save(event:React.FormEvent){
    event.preventDefault();if(saving||reason.trim().length<10)return
    setSaving(true);setError('')
    try{await apiFetch(`/admin/users/${item.id}/status`,{method:'POST',body:JSON.stringify({status:decision,reason:reason.trim()})});onSaved(decision==='suspended'?`${item.name} is suspended and signed out everywhere.`:`${item.name} can sign in again. Truck and driver eligibility needs a separate review.`)}
    catch(failure){setError(failure instanceof Error?failure.message:'Status change failed')}
    finally{setSaving(false)}
  }
  return <article className="admin-record">
    <div><b>{item.name}</b><small>{item.email} · {item.roles.join(', ')} · {item.status} · email {item.email_verified?'verified':'unverified'}</small></div>
    {privileged(item)?<small className="admin-note">Admin accounts are managed separately.</small>:<div className="admin-actions">
      {!open&&<button className="secondary" disabled={busy} onClick={onOpen}>Change account status</button>}
      {onDriverReview&&item.roles.includes('driver')&&<button className="secondary" disabled={busy||item.status!=='active'} onClick={onDriverReview}>Review driver reactivation</button>}
    </div>}
    {open&&!privileged(item)&&<form className="admin-status-form" onSubmit={save} onKeyDown={event=>{if(event.key==='Escape'&&!saving)onClose()}}>
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

export default function AdminRecords(){
  const [tab,setTab]=useState<Tab>('users'),[q,setQ]=useState(''),[search,setSearch]=useState(''),[page,setPage]=useState(1)
  const [data,setData]=useState<Page<User|Booking|Requirement>|null>(null),[state,setState]=useState('loading'),[message,setMessage]=useState('')
  const [selected,setSelected]=useState<string|null>(null),[busy,setBusy]=useState(false)
  const [driverReview,setDriverReview]=useState<User|null>(null),[driverReason,setDriverReason]=useState('')
  async function reactivateDriver(event:React.FormEvent){event.preventDefault();if(!driverReview||busy||driverReason.trim().length<10)return;setBusy(true);try{await apiFetch(`/admin/users/${driverReview.id}/driver-reactivation`,{method:'POST',body:JSON.stringify({reason:driverReason.trim()})});setDriverReview(null);setDriverReason('');setMessage('Driver eligibility restored after server-side identity, licence and scan checks.');await load()}catch(error){setMessage(error instanceof Error?error.message:'Driver review failed')}finally{setBusy(false)}}
  async function load(){setState('loading');try{setData(await apiFetch<Page<User|Booking|Requirement>>(`/admin/${tab}?q=${encodeURIComponent(search)}&page=${page}&page_size=25`));setState('ready')}catch(error){setState(error instanceof ApiError&&[401,403].includes(error.status)?'forbidden':'error')}}
  useEffect(()=>{void load()},[tab,search,page])
  return <section className="panel admin-records"><h2>Operational records</h2><div className="fleet-tabs" role="group" aria-label="Record type">{TABS.map(([value,label])=><button key={value} aria-pressed={tab===value} className={tab===value?'active':undefined} onClick={()=>{setTab(value);setPage(1);setSelected(null);setMessage('')}}>{label}</button>)}</div>
    <form className="admin-search" onSubmit={event=>{event.preventDefault();setSearch(q);setPage(1)}}><label>{SEARCH_LABEL[tab]}<input maxLength={100} value={q} onChange={event=>setQ(event.target.value)}/></label><button>Search</button></form>
    {state==='loading'&&<p role="status">Loading operational records…</p>}{state==='forbidden'&&<p role="alert">Administrator access required.</p>}{state==='error'&&<button onClick={load}>Retry records</button>}{message&&<p role="status">{message}</p>}
    {state==='ready'&&data&&<><div className="admin-record-list">{data.items.map(item=>'roles' in item
      ?<UserRow key={item.id} item={item} open={selected===item.id} busy={busy} onOpen={()=>{setSelected(item.id);setDriverReview(null);setMessage('')}} onClose={()=>setSelected(null)} onSaved={text=>{setSelected(null);setMessage(text);void load()}} onDriverReview={()=>{setDriverReview(item);setDriverReason('');setSelected(null)}}/>
      :'route' in item?<RequirementRow key={item.id} item={item}/>
      :<article key={item.id} className="admin-record"><div><b>{item.reference}</b><small>{item.customer_name} · {item.status} · ₹{item.total_amount}</small></div></article>)}{!data.items.length&&<p>No matching records.</p>}</div>
      <p>Page {page} · {data.total} matching records</p><div className="admin-actions"><button className="secondary" disabled={page<=1} onClick={()=>setPage(value=>value-1)}>Previous page</button><button className="secondary" disabled={page*data.page_size>=data.total} onClick={()=>setPage(value=>value+1)}>Next page</button></div></>}
    {driverReview&&<form className="fleet-form" onSubmit={reactivateDriver}><h3>Driver reactivation: {driverReview.name}</h3><p>This is separate from account activation. The API requires current accepted, version-pinned, clean-scanned identity documents, a current licence and an active verified transport provider.</p><label>Driver review reason<textarea required disabled={busy} minLength={10} maxLength={2000} value={driverReason} onChange={event=>setDriverReason(event.target.value)}/></label><button disabled={busy||driverReason.trim().length<10}>Confirm driver reactivation</button><button type="button" disabled={busy} onClick={()=>setDriverReview(null)}>Cancel driver review</button></form>}
  </section>
}
