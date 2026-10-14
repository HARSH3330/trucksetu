import {useEffect,useState} from 'react'
import {apiFetch,ApiError} from '../lib/api'

type User={id:string;name:string;email:string;status:string;roles:string[];email_verified:boolean}
type Booking={id:string;reference:string;customer_name:string;status:string;total_amount:string}
type Page<T>={items:T[];page:number;page_size:number;total:number}
export default function AdminRecords(){
  const [tab,setTab]=useState<'users'|'bookings'>('users'),[q,setQ]=useState(''),[search,setSearch]=useState(''),[page,setPage]=useState(1)
  const [data,setData]=useState<Page<User|Booking>|null>(null),[state,setState]=useState('loading'),[message,setMessage]=useState('')
  const [selected,setSelected]=useState<User|null>(null),[decision,setDecision]=useState<'active'|'suspended'>('suspended'),[reason,setReason]=useState(''),[busy,setBusy]=useState(false)
  async function load(){setState('loading');try{setData(await apiFetch<Page<User|Booking>>(`/admin/${tab}?q=${encodeURIComponent(search)}&page=${page}&page_size=25`));setState('ready')}catch(error){setState(error instanceof ApiError&&[401,403].includes(error.status)?'forbidden':'error')}}
  useEffect(()=>{void load()},[tab,search,page])
  async function changeStatus(event:React.FormEvent){
    event.preventDefault();if(!selected||busy||reason.trim().length<10)return
    if(!window.confirm(`Confirm ${decision} for this account? Sessions will be revoked. Reactivation will not restore supply eligibility.`))return
    setBusy(true)
    try{await apiFetch(`/admin/users/${selected.id}/status`,{method:'POST',body:JSON.stringify({status:decision,reason})});setSelected(null);setReason('');setMessage('Account status audited; sessions revoked. Supply reactivation requires separate review.');await load()}
    catch(error){setMessage(error instanceof Error?error.message:'Status change failed')}
    finally{setBusy(false)}
  }
  return <section className="panel"><h2>Operational records</h2><div className="fleet-tabs">{(['users','bookings'] as const).map(value=><button key={value} onClick={()=>{setTab(value);setPage(1);setSelected(null)}}>{value}</button>)}</div>
    <form onSubmit={event=>{event.preventDefault();setSearch(q);setPage(1)}}><label>{tab==='users'?'Search name or email':'Search booking reference'}<input maxLength={100} value={q} onChange={event=>setQ(event.target.value)}/></label><button>Search</button></form>
    {state==='loading'&&<p role="status">Loading operational records…</p>}{state==='forbidden'&&<p role="alert">Administrator access required.</p>}{state==='error'&&<button onClick={load}>Retry records</button>}{message&&<p role="status">{message}</p>}
    {state==='ready'&&data&&<><div className="fleet-list">{data.items.map(item=>'roles' in item?<article key={item.id}><div><b>{item.name}</b><small>{item.email} · {item.roles.join(', ')} · {item.status} · email {item.email_verified?'verified':'unverified'}</small></div>{!item.roles.some(role=>['admin','superadmin'].includes(role))&&<button onClick={()=>{setSelected(item);setReason('');setDecision(item.status==='active'?'suspended':'active')}}>Change account status</button>}</article>:<article key={item.id}><div><b>{item.reference}</b><small>{item.customer_name} · {item.status} · ₹{item.total_amount}</small></div></article>)}{!data.items.length&&<p>No matching records.</p>}</div><p>Page {page} · {data.total} matching records</p><button disabled={page<=1} onClick={()=>setPage(value=>value-1)}>Previous page</button><button disabled={page*data.page_size>=data.total} onClick={()=>setPage(value=>value+1)}>Next page</button></>}
    {selected&&<form className="fleet-form" onSubmit={changeStatus}><h3>Change status: {selected.name}</h3><p>This invalidates sessions. Supply reactivation needs a separate review; privileged accounts are excluded.</p><label>Account status<select value={decision} onChange={event=>setDecision(event.target.value as 'active'|'suspended')}><option value="suspended">Suspend</option><option value="active">Reactivate account only</option></select></label><label>Required reason<textarea required minLength={10} maxLength={2000} value={reason} onChange={event=>setReason(event.target.value)}/></label><button disabled={busy||reason.trim().length<10}>Confirm status change</button><button type="button" disabled={busy} onClick={()=>setSelected(null)}>Cancel</button></form>}
  </section>
}
