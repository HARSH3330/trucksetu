import {useEffect,useState} from 'react'
import {apiFetch,type CurrentUser} from '../lib/api'
import LiveKYC from './LiveKYC'
import './DemandMarketplace.css'

type Doc={id:string;type:string;status:string}
type Application={id:string;status:string;policy_version:string;consent_sha256:string|null;required_documents:string[];decision_reason:string|null;documents:Doc[]}
type Policy={version:string;required_documents:string[];consent_text:string;consent_sha256:string}
type Pending={document_type:string;filename:string;content_type:string;storage_key:string}
const label=(value:string)=>({aadhaar:'Aadhaar',pan:'PAN'}[value]||value)
const errorText=(error:unknown)=>error instanceof Error?error.message:'Verification is unavailable. Your uploaded document has not been approved.'

export default function VerificationWorkspace(){
 const [user,setUser]=useState<CurrentUser|null>(null),[error,setError]=useState('')
 const load=()=>{setError('');apiFetch<CurrentUser>('/auth/me').then(setUser).catch(e=>setError(errorText(e)))}
 useEffect(load,[])
 if(error)return <main className="page"><p role="alert">{error}</p><button onClick={load}>Retry verification</button></main>
 if(!user)return <main className="page"><p role="status">Loading verification…</p></main>
 if(user.roles.some(r=>['admin','superadmin'].includes(r)))return <><LiveKYC/><CustomerVerification admin/></>
 return user.roles.includes('customer')?<CustomerVerification/>:<LiveKYC/>
}

export function CustomerVerification({admin=false}:{admin?:boolean}){
 const [policy,setPolicy]=useState<Policy|null>(null),[item,setItem]=useState<Application|null>(null),[queue,setQueue]=useState<Application[]>([])
 const [message,setMessage]=useState(''),[error,setError]=useState(''),[loading,setLoading]=useState(true),[busy,setBusy]=useState(false)
 const [consent,setConsent]=useState(false),[pending,setPending]=useState<Pending|null>(null),[reason,setReason]=useState(''),[decisions,setDecisions]=useState<Record<string,string>>({}),[decision,setDecision]=useState('verified'),[filter,setFilter]=useState('under_review')
 async function load(){
  setLoading(true);setError('')
  try{
   if(admin)setQueue(await apiFetch<Application[]>(`/customer-kyc/admin/applications?status=${filter}`))
   else{const [p,a]=await Promise.all([apiFetch<Policy>('/customer-kyc/policy'),apiFetch<Application|null>('/customer-kyc/me')]);setPolicy(p);setItem(a)}
  }catch(e){setError(errorText(e))}finally{setLoading(false)}
 }
 useEffect(()=>{void load()},[admin,filter])
 async function action(fn:()=>Promise<void>){if(busy)return;setBusy(true);setMessage('');try{await fn()}catch(e){setMessage(errorText(e))}finally{setBusy(false)}}
 async function start(){
  if(!policy||!consent)return
  setItem(await apiFetch<Application>('/customer-kyc/applications',{method:'POST',body:JSON.stringify({consent_version:policy.version,consent_sha256:policy.consent_sha256})}))
  setConsent(false);setMessage('Application created. Upload the required documents.')
 }
 async function open(id:string){await action(async()=>{const result=await apiFetch<{download_url:string}>(`/customer-kyc/documents/${id}/download`);window.open(result.download_url,'_blank','noopener,noreferrer')})}
 async function finalize(value:Pending){await apiFetch('/customer-kyc/documents',{method:'POST',body:JSON.stringify(value)});setPending(null);await load();setMessage('Scan verified. Document registered for manual review.')}
 async function upload(kind:string,file:File){
  await action(async()=>{
   if(file.size===0||file.size>10*1024*1024)throw Error('Choose a document between 1 byte and 10 MB.')
   if(!['application/pdf','image/png','image/jpeg'].includes(file.type))throw Error('Choose a PDF, PNG or JPEG document.')
   const request={document_type:kind,filename:file.name,content_type:file.type}
   const signed=await apiFetch<{storage_key:string;upload_url:string}>('/customer-kyc/uploads',{method:'POST',body:JSON.stringify(request)})
   const response=await fetch(signed.upload_url,{method:'PUT',headers:{'Content-Type':file.type,'x-amz-server-side-encryption':'AES256'},body:file})
   if(!response.ok)throw Error('Private upload failed. Try again.')
   const value={...request,storage_key:signed.storage_key};setPending(value)
   await finalize(value)
  })
 }
 const renewal=Boolean(item&&policy&&(item.policy_version!==policy.version||item.consent_sha256!==policy.consent_sha256||[...item.required_documents].sort().join(',')!==[...policy.required_documents].sort().join(',')))
 const canStart=!item||renewal||['rejected','suspended'].includes(item.status)
 const active=admin?queue.find(q=>q.id===item?.id)||null:item
 const allAccepted=Boolean(active&&active.required_documents.every(kind=>active.documents.some(d=>d.type===kind&&d.status!=='rejected'&&decisions[d.id]==='accepted')))
 return <section className="page demand-page customer-verification" aria-busy={loading||busy}>
  {admin?<h2>Customer document review</h2>:<h1>Customer verification</h1>}
  <p>Private documents must pass malware scanning, then an authorised reviewer checks each required document. A clean scan does not verify your identity.</p>
  {message&&<p role="status">{message}</p>}
  {loading?<p role="status">Loading customer verification…</p>:error?<div role="alert"><p>{error}</p><button onClick={()=>void load()}>Retry customer verification</button></div>:<>
   {admin?<>
    <label>Customer application status<select value={filter} onChange={e=>{setFilter(e.target.value);setItem(null);setDecisions({});setReason('')}}>{['under_review','verified','rejected','resubmit_required','suspended'].map(v=><option value={v} key={v}>{v.replaceAll('_',' ')}</option>)}</select></label>
    <div className="demand-actions">{queue.map(q=><button key={q.id} aria-pressed={item?.id===q.id} onClick={()=>{setItem(q);setDecisions({});setReason('');setDecision(q.status==='verified'?'suspended':'verified')}}>Application {q.id.slice(0,8)} · {q.status.replaceAll('_',' ')}</button>)}</div>
    {!queue.length&&<p>No customer applications in this queue.</p>}
   </>:<>
    {canStart&&policy&&<fieldset className="customer-consent"><legend>Customer document consent</legend>
     <p>Required documents: {policy.required_documents.map(label).join(', ')}.</p>
     <p className="consent-text">{policy.consent_text}</p><p>Policy version: {policy.version}. <a href="#privacy">Read the privacy policy</a>.</p>
     <label className="demand-check"><input type="checkbox" checked={consent} onChange={e=>setConsent(e.target.checked)}/>I have read this customer document consent and agree to the stated review.</label>
     <button disabled={busy||!consent} onClick={()=>void action(start)}>{item?'Start a fresh customer review':'Start customer verification'}</button>
    </fieldset>}
    {item&&!renewal&&['registered','resubmit_required'].includes(item.status)&&<>
     {item.required_documents.map(kind=><label key={kind}>{label(kind)}<input aria-label={`Upload ${label(kind)}`} type="file" accept="application/pdf,image/png,image/jpeg" disabled={busy||Boolean(pending)||item.documents.some(d=>d.type===kind&&d.status!=='rejected')} onChange={e=>{const file=e.target.files?.[0];if(file)void upload(kind,file);e.target.value=''}}/></label>)}
     {pending&&<div><p>The private upload is waiting for a verified clean scan. It has not been submitted for approval.</p><button disabled={busy} onClick={()=>void action(()=>finalize(pending))}>Check scan and register document</button></div>}
     <button disabled={busy||Boolean(pending)||!item.required_documents.every(kind=>item.documents.some(d=>d.type===kind&&d.status!=='rejected'))} onClick={()=>void action(async()=>{setItem(await apiFetch<Application>('/customer-kyc/submit',{method:'POST'}));setMessage('Submitted for manual review. Publication remains blocked until approval.')})}>Submit customer documents for review</button>
    </>}
   </>}
   {active&&<><h2>Application: {active.status.replaceAll('_',' ')}</h2>{active.decision_reason&&<p>Review reason: {active.decision_reason}</p>}
    <ul>{active.documents.map(d=><li key={d.id}><b>{label(d.type)}</b> · {d.status} <button disabled={busy} onClick={()=>void open(d.id)}>Open {label(d.type)} securely</button>
     {admin&&active.status==='under_review'&&d.status!=='rejected'&&<label>Decision for {label(d.type)}<select value={decisions[d.id]||''} onChange={e=>setDecisions({...decisions,[d.id]:e.target.value})}><option value="">Review document first</option><option value="accepted">Accept</option><option value="rejected">Reject</option></select></label>}
    </li>)}</ul>
    {admin&&['under_review','verified'].includes(active.status)&&<>
     <label>Customer review decision<select value={decision} onChange={e=>setDecision(e.target.value)}>{active.status==='under_review'?<><option value="verified">Verify</option><option value="resubmit_required">Request resubmission</option><option value="rejected">Reject</option></>:<option value="suspended">Suspend</option>}</select></label>
     <label>Customer review reason<textarea value={reason} minLength={10} maxLength={2000} onChange={e=>setReason(e.target.value)}/></label>
     {decision==='verified'&&!allAccepted&&<p>Accept every required document after reviewing it before verifying this application.</p>}
     <button disabled={busy||reason.trim().length<10||(decision==='verified'&&!allAccepted)} onClick={()=>void action(async()=>{await apiFetch(`/customer-kyc/admin/applications/${active.id}/review`,{method:'POST',body:JSON.stringify({decision,reason,document_decisions:Object.fromEntries(Object.entries(decisions).filter(([,v])=>v))})});setItem(null);await load();setMessage('Customer review recorded.')})}>Record customer review</button>
    </>}
   </>}
   <button className="secondary" disabled={busy} onClick={()=>void load()}>Refresh customer verification</button>
  </>}
 </section>
}
