import {useEffect,useState} from 'react'
import {apiFetch,ApiError} from '../lib/api'

type Document={id:string;type:string;filename:string;status:string;expires_on:string;review_reason:string|null}
type Pending={document_type:string;filename:string;content_type:string;storage_key:string;expires_on:string}
const kinds=['rc','insurance','fitness','pollution','permit']
export default function VehicleDocuments({vehicleId,admin=false}:{vehicleId:string;admin?:boolean}){
  const [items,setItems]=useState<Document[]>([]),[state,setState]=useState('loading'),[message,setMessage]=useState('')
  const [kind,setKind]=useState('rc'),[file,setFile]=useState<File|null>(null),[expiry,setExpiry]=useState('')
  const [pending,setPending]=useState<Pending|null>(null),[busy,setBusy]=useState(false),[reason,setReason]=useState('')
  const path=`/carrier-vehicles/${vehicleId}`
  async function load(){setState('loading');try{setItems(await apiFetch<Document[]>(`${path}/documents`));setState('ready')}catch(error){setState(error instanceof ApiError&&[401,403,404].includes(error.status)?'forbidden':'error')}}
  useEffect(()=>{void load()},[vehicleId])
  async function complete(payload:Pending){
    try{await apiFetch(`${path}/documents`,{method:'POST',body:JSON.stringify(payload)});setPending(null);setFile(null);setMessage('Clean-scanned file registered, awaiting manual acceptance.');await load()}
    catch(error){if(error instanceof ApiError&&error.status===409&&error.message.includes('scan'))setPending(payload);setMessage(error instanceof Error?error.message:'Registration failed')}
  }
  async function upload(event:React.FormEvent){
    event.preventDefault();if(!file||busy)return
    if(file.size<=0||file.size>10*1024*1024||!['application/pdf','image/jpeg','image/png'].includes(file.type)){setMessage('Choose a PDF, JPEG or PNG between 1 byte and 10 MB.');return}
    setBusy(true)
    try{const prepared=await apiFetch<{upload_url:string;storage_key:string}>(`${path}/uploads`,{method:'POST',body:JSON.stringify({document_type:kind,filename:file.name,content_type:file.type})});const response=await fetch(prepared.upload_url,{method:'PUT',headers:{'Content-Type':file.type,'x-amz-server-side-encryption':'AES256'},body:file});if(!response.ok)throw new Error('Private upload failed.');await complete({document_type:kind,filename:file.name,content_type:file.type,storage_key:prepared.storage_key,expires_on:expiry})}
    catch(error){setMessage(error instanceof Error?error.message:'Upload unavailable')}
    finally{setBusy(false)}
  }
  async function action(document:Document,status?:'accepted'|'rejected'){
    setBusy(true);setMessage('')
    try{
      if(status){await apiFetch(`/admin${path}/${'documents'}/${document.id}/review`,{method:'POST',body:JSON.stringify({status,reason})});setMessage('Document decision saved and audit logged.');await load()}
      else{const result=await apiFetch<{download_url:string}>(`${path}/documents/${document.id}/download`);window.open(result.download_url,'_blank','noopener,noreferrer')}
    }catch(error){setMessage(error instanceof Error?error.message:'Document action failed')}
    finally{setBusy(false)}
  }
  return <section className="panel"><h3>Private vehicle documents</h3><p>RC, insurance, fitness, pollution and permit require clean scans and separate manual acceptance. Existing metadata approval is not file verification.</p>
    {state==='loading'&&<p role="status">Loading protected documents…</p>}{state==='error'&&<button onClick={load}>Retry documents</button>}{state==='forbidden'&&<p role="alert">Document access unavailable for this account.</p>}
    {message&&<p role="status">{message}</p>}
    {state==='ready'&&<><div className="document-list">{items.map(item=><article key={item.id}><div><b>{item.type}: {item.filename}</b><small>{item.status} · expires {item.expires_on}</small>{item.review_reason&&<small>{item.review_reason}</small>}</div><button disabled={busy} onClick={()=>void action(item)}>View protected file</button>{admin&&item.status!=='rejected'&&<><button disabled={busy||reason.trim().length<10} onClick={()=>void action(item,'accepted')}>Accept document</button><button disabled={busy||reason.trim().length<10} onClick={()=>void action(item,'rejected')}>Reject document</button></>}</article>)}{!items.length&&<p>No vehicle documents registered.</p>}</div>
    {admin?<label>Document review reason<textarea required minLength={10} maxLength={2000} value={reason} onChange={event=>setReason(event.target.value)}/></label>:<form className="fleet-form" onSubmit={upload}><label>Document type<select disabled={busy||Boolean(pending)} value={kind} onChange={event=>setKind(event.target.value)}>{kinds.map(value=><option key={value}>{value}</option>)}</select></label><label>Document expiry<input type="date" required value={expiry} disabled={busy||Boolean(pending)} onChange={event=>setExpiry(event.target.value)}/></label><label>Harmless test or genuine authorised vehicle file<input type="file" required accept=".pdf,.jpg,.jpeg,.png" disabled={busy||Boolean(pending)} onChange={event=>setFile(event.target.files?.[0]||null)}/></label><button disabled={busy||Boolean(pending)}>Upload private document</button></form>}
    {pending&&<button disabled={busy} onClick={async()=>{setBusy(true);try{await complete(pending)}finally{setBusy(false)}}}>Check scan again</button>}</>}
  </section>
}
