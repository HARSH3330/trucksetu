import {useEffect,useState} from 'react'
import {BadgeCheck,FileText} from 'lucide-react'
import {ApiError,apiFetch,type CurrentUser} from '../lib/api'
import LiveKYC from './LiveKYC'
import './DemandMarketplace.css'

type Doc={id:string;type:string;status:string}
type Application={id:string;status:string;policy_version:string;consent_sha256:string|null;required_documents:string[];decision_reason:string|null;documents:Doc[];account_name?:string;account_email?:string}
/** Admin queue rows carry the account holder; a customer's own view does not. */
export const applicationTitle=(item:{id:string;account_name?:string})=>`${item.account_name?item.account_name+' · ':''}Application ${item.id.slice(0,8)}`
type Policy={version:string;required_documents:string[];consent_text:string;consent_sha256:string}
type Pending={document_type:string;filename:string;content_type:string;storage_key:string}
const label=(value:string)=>({aadhaar:'Aadhaar',pan:'PAN'}[value]||value)
const errorText=(error:unknown)=>error instanceof Error?error.message:'Verification is unavailable. Your uploaded document has not been approved.'

export function VerificationSignedOut({onSignIn}:{onSignIn?:()=>void}){
 return <main className="page"><h1>Customer verification</h1><p>Sign in to verify your account. Your PAN is reviewed privately and is never shown to providers.</p>{onSignIn&&<button onClick={onSignIn}>Sign in</button>}</main>
}

export default function VerificationWorkspace({onSignIn}:{onSignIn?:()=>void}={}){
 const [user,setUser]=useState<CurrentUser|null>(null),[error,setError]=useState(''),[signedOut,setSignedOut]=useState(false)
 const load=()=>{setError('');setSignedOut(false);apiFetch<CurrentUser>('/auth/me').then(setUser).catch(e=>{if(e instanceof ApiError&&e.status===401)setSignedOut(true);else setError(errorText(e))})}
 useEffect(load,[])
 if(signedOut)return <VerificationSignedOut onSignIn={onSignIn}/>
 if(error)return <main className="page"><p role="alert">{error}</p><button onClick={load}>Retry verification</button></main>
 if(!user)return <main className="page"><p role="status">Loading verification…</p></main>
 if(user.roles.some(r=>['admin','superadmin'].includes(r)))return <AdminVerification/>
 return user.roles.includes('customer')?<CustomerVerification/>:<LiveKYC/>
}

/** One page for both review queues; customer PAN reviews come first because they are the most frequent. */
export function AdminVerification(){
 return <main className="page admin-verification">
  <div className="page-title"><span className="kicker">MANUAL ADMIN VERIFICATION</span><h1>Verification review queue</h1><p>Open each scan-clean document, record a decision and give a reason. Customers need their PAN accepted; truck owners and drivers need their full document set.</p></div>
  <CustomerVerification admin/>
  <LiveKYC embedded/>
 </main>
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
 const select=(q:Application)=>{setItem(q);setDecisions({});setReason('');setDecision(q.status==='verified'?'suspended':'verified')}
 if(admin)return <section className="panel customer-verification customer-review" aria-busy={loading||busy}>
  <h2>Customer document review</h2>
  <p className="customer-review-intro">Customers upload a PAN that must pass the malware scan. Open it, accept it, then verify the application. A clean scan alone does not verify identity.</p>
  {message&&<p role="status" className="privacy-banner">{message}</p>}
  {loading?<p role="status">Loading customer verification…</p>:error?<div role="alert"><p>{error}</p><button onClick={()=>void load()}>Retry customer verification</button></div>:<>
   <div className="customer-review-bar">
    <label>Customer application status<select value={filter} onChange={e=>{setFilter(e.target.value);setItem(null);setDecisions({});setReason('')}}>{['under_review','verified','rejected','resubmit_required','suspended'].map(v=><option value={v} key={v}>{v.replaceAll('_',' ')}</option>)}</select></label>
    <button className="secondary" disabled={busy} onClick={()=>void load()}>Refresh customer verification</button>
   </div>
   <div className="kyc-admin-grid">
    <aside className="kyc-queue">{queue.map(q=><button key={q.id} className={item?.id===q.id?'active':''} aria-pressed={item?.id===q.id} onClick={()=>select(q)}><span aria-hidden="true">{q.documents.length}</span><div><b>{applicationTitle(q)}</b><small>{q.account_email&&<>{q.account_email} · </>}{q.status.replaceAll('_',' ')} ·{q.documents.map(d=>label(d.type)).join(', ')||'No documents'}</small></div></button>)}
     {!queue.length&&<div className="empty-state">No customer applications in this queue.</div>}</aside>
    {active?<div className="kyc-review customer-review-panel">
     <div className="panel-head"><div><span className="badge">{active.status.replaceAll('_',' ')}</span><h3>{applicationTitle(active)}</h3>{active.account_email&&<p>{active.account_email}</p>}{active.decision_reason&&<p>Review reason: {active.decision_reason}</p>}</div></div>
     <div className="document-list">{active.documents.map(d=><article key={d.id}><span><FileText/></span><div><b>{label(d.type)}</b><small>{d.status}</small></div>
      <button type="button" disabled={busy} onClick={()=>void open(d.id)}>Open {label(d.type)} securely</button>
      {active.status==='under_review'&&d.status!=='rejected'&&<select aria-label={`Decision for ${label(d.type)}`} value={decisions[d.id]||''} onChange={e=>setDecisions({...decisions,[d.id]:e.target.value})}><option value="">Review document first</option><option value="accepted">Accept</option><option value="rejected">Reject</option></select>}
     </article>)}</div>
     {['under_review','verified'].includes(active.status)&&<div className="customer-review-form">
      <label>Customer review decision<select value={decision} onChange={e=>setDecision(e.target.value)}>{active.status==='under_review'?<><option value="verified">Verify</option><option value="resubmit_required">Request resubmission</option><option value="rejected">Reject</option></>:<option value="suspended">Suspend</option>}</select></label>
      <label>Customer review reason<textarea value={reason} minLength={10} maxLength={2000} placeholder="At least 10 characters, e.g. PAN checked and matches the account" onChange={e=>setReason(e.target.value)}/></label>
      {decision==='verified'&&!allAccepted&&<p className="customer-review-hint">Set every document to Accept before verifying.</p>}
      <button disabled={busy||reason.trim().length<10||(decision==='verified'&&!allAccepted)} onClick={()=>void action(async()=>{await apiFetch(`/customer-kyc/admin/applications/${active.id}/review`,{method:'POST',body:JSON.stringify({decision,reason,document_decisions:Object.fromEntries(Object.entries(decisions).filter(([,v])=>v))})});setItem(null);await load();setMessage('Customer review recorded.')})}><BadgeCheck/>Record customer review</button>
     </div>}
    </div>:queue.length>0&&<div className="empty-state">Select an application to review its PAN.</div>}
   </div>
  </>}
 </section>
 return <section className="page demand-page customer-verification" aria-busy={loading||busy}>
  <h1>Customer verification</h1>
  <p>Private documents must pass malware scanning, then an authorised reviewer checks each required document. A clean scan does not verify your identity.</p>
  {message&&<p role="status">{message}</p>}
  {loading?<p role="status">Loading customer verification…</p>:error?<div role="alert"><p>{error}</p><button onClick={()=>void load()}>Retry customer verification</button></div>:<>
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
   {active&&<><h2>Application: {active.status.replaceAll('_',' ')}</h2>{active.decision_reason&&<p>Review reason: {active.decision_reason}</p>}
    <ul>{active.documents.map(d=><li key={d.id}><b>{label(d.type)}</b> · {d.status} <button disabled={busy} onClick={()=>void open(d.id)}>Open {label(d.type)} securely</button></li>)}</ul>
   </>}
   <button className="secondary" disabled={busy} onClick={()=>void load()}>Refresh customer verification</button>
  </>}
 </section>
}
