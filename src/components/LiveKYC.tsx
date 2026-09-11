import {useEffect, useMemo, useState} from 'react'
import {AlertTriangle, BadgeCheck, Check, FileText, ShieldCheck, UploadCloud, X} from 'lucide-react'
import {ApiError, apiFetch, type CurrentUser} from '../lib/api'
import './LiveKYC.css'

type Document={id:string;type:string;filename:string;status:string;expires_on:string|null}
type Application={id:string;provider_id:string;provider_name:string|null;provider_type:string|null;status:string;legal_name:string;submitted_at:string|null;decision_reason:string|null;documents:Document[]}
type Expiring={id:string;type:string;expires_on:string;status:string}
const labels:Record<string,string>={aadhaar:'Aadhaar',pan:'PAN',driving_licence:'Driving licence',vehicle_rc:'Vehicle RC',gst_certificate:'GST certificate',bank_proof:'Bank proof',vehicle_insurance:'Vehicle insurance',fitness_certificate:'Fitness certificate',commercial_permit:'Commercial permit',pollution_certificate:'Pollution certificate'}

export default function LiveKYC(){
  const [user,setUser]=useState<CurrentUser|null>(null)
  const [application,setApplication]=useState<Application|null>(null)
  const [queue,setQueue]=useState<Application[]>([])
  const [expiring,setExpiring]=useState<Expiring[]>([])
  const [selected,setSelected]=useState('')
  const [filter,setFilter]=useState('under_review')
  const [state,setState]=useState<'loading'|'ready'|'signed-out'|'error'>('loading')
  const [message,setMessage]=useState('')
  const [legalName,setLegalName]=useState('')
  const [providerType,setProviderType]=useState('driver')
  const [pan,setPan]=useState('')
  const [gstin,setGstin]=useState('')
  const [decision,setDecision]=useState('verified')
  const [reason,setReason]=useState('Documents reviewed manually and details match the application.')
  const [documentDecisions,setDocumentDecisions]=useState<Record<string,'accepted'|'rejected'>>({})

  const admin=Boolean(user?.roles.some(role=>['admin','superadmin'].includes(role)))
  const current=useMemo(()=>queue.find(item=>item.id===selected)||queue[0]||null,[queue,selected])

  async function loadQueue(statusValue=filter){
    const [items,expiry]=await Promise.all([apiFetch<Application[]>(`/kyc/admin/applications?status=${statusValue}`),apiFetch<Expiring[]>('/kyc/admin/expiring-documents?days=30')])
    setQueue(items);setExpiring(expiry);setSelected(items[0]?.id||'')
  }
  async function load(){
    setState('loading')
    try{
      const profile=await apiFetch<CurrentUser>('/auth/me');setUser(profile)
      if(profile.roles.some(role=>['admin','superadmin'].includes(role)))await loadQueue()
      else{try{setApplication(await apiFetch<Application>('/kyc/applications/me'))}catch(error){if(!(error instanceof ApiError&&error.status===404))throw error}}
      setState('ready')
    }catch(error){setState(error instanceof ApiError&&error.status===401?'signed-out':'error')}
  }
  useEffect(()=>{void load()},[])
  useEffect(()=>{if(current)setDocumentDecisions(Object.fromEntries(current.documents.map(document=>[document.type,'accepted'])));else setDocumentDecisions({})},[current])

  async function createApplication(event:React.FormEvent){
    event.preventDefault();setMessage('Creating verification application…')
    try{setApplication(await apiFetch<Application>('/kyc/applications',{method:'POST',body:JSON.stringify({legal_name:legalName,provider_type:providerType,pan_last_four:pan||null,gstin:gstin||null})}));setMessage('Application created. Document upload will be enabled after private storage is configured.')}
    catch(error){setMessage(error instanceof Error?error.message:'Application could not be created')}
  }
  async function submitApplication(){
    if(!application)return
    try{setApplication(await apiFetch<Application>(`/kyc/applications/${application.id}/submit`,{method:'POST'}));setMessage('Application submitted for manual review.')}
    catch(error){setMessage(error instanceof Error?error.message:'Application could not be submitted')}
  }
  async function review(){
    if(!current)return
    setMessage('Recording review…')
    try{await apiFetch(`/kyc/admin/applications/${current.id}/review`,{method:'POST',body:JSON.stringify({decision,reason,document_decisions:documentDecisions})});await loadQueue();setMessage('Review decision recorded in the audit trail.')}
    catch(error){setMessage(error instanceof Error?error.message:'Review could not be recorded')}
  }

  if(state==='loading')return <main className="page"><div className="empty-state">Loading verification workspace…</div></main>
  if(state==='signed-out')return <main className="page"><div className="empty-state"><b>Sign in required</b><p>Verification records are private.</p></div></main>
  if(state==='error')return <main className="page"><div className="empty-state"><b>Verification workspace unavailable</b><button onClick={load}>Retry</button></div></main>
  if(admin)return <main className="page"><div className="page-title"><span className="kicker">MANUAL ADMIN VERIFICATION</span><h1>Verification review queue</h1><p>Review metadata and record auditable decisions. Document files remain unavailable until private storage is configured.</p></div>{message&&<div className="privacy-banner">{message}</div>}<div className="kyc-summary"><span><b>{queue.length}</b><small>{filter.replaceAll('_',' ')}</small></span><span><b>{expiring.filter(x=>x.status==='expired').length}</b><small>Expired documents</small></span><span><b>{expiring.filter(x=>x.status==='expiring').length}</b><small>Expiring within 30 days</small></span></div><div className="kyc-filter"><select value={filter} onChange={async e=>{setFilter(e.target.value);await loadQueue(e.target.value)}}><option value="under_review">Under review</option><option value="verified">Verified</option><option value="resubmit_required">Resubmission required</option><option value="rejected">Rejected</option><option value="suspended">Suspended</option></select></div><div className="kyc-admin-grid"><aside className="kyc-queue">{queue.map(item=><button className={current?.id===item.id?'active':''} onClick={()=>setSelected(item.id)} key={item.id}><span>{(item.provider_name||item.legal_name).split(' ').map(x=>x[0]).join('').slice(0,2)}</span><div><b>{item.provider_name||item.legal_name}</b><small>{item.provider_type} · {item.documents.length} documents</small><em>{item.submitted_at?new Date(item.submitted_at).toLocaleString('en-IN'):'Not submitted'}</em></div></button>)}{!queue.length&&<div className="empty-state">No applications in this queue.</div>}</aside>{current&&<section className="panel kyc-review"><div className="panel-head"><div><span className="badge">{current.status.replaceAll('_',' ')}</span><h2>{current.legal_name}</h2><p>{current.provider_type} · {current.provider_name}</p></div></div><div className="kyc-risk"><AlertTriangle/><span><b>Storage status</b><small>Only privacy-safe metadata is shown. File viewing requires private object storage.</small></span></div><div className="document-list">{current.documents.map(document=><article key={document.id}><span><FileText/></span><div><b>{labels[document.type]||document.type}</b><small>{document.filename}</small></div><em>{document.expires_on||'No expiry'}</em><select value={documentDecisions[document.type]||'accepted'} onChange={e=>setDocumentDecisions({...documentDecisions,[document.type]:e.target.value as 'accepted'|'rejected'})}><option value="accepted">Accept</option><option value="rejected">Reject</option></select></article>)}{!current.documents.length&&<div className="empty-state">No documents registered.</div>}</div>{current.status==='under_review'&&<div className="review-form"><select value={decision} onChange={e=>setDecision(e.target.value)}><option value="verified">Verify</option><option value="resubmit_required">Request resubmission</option><option value="rejected">Reject</option><option value="suspended">Suspend</option></select><textarea minLength={5} value={reason} onChange={e=>setReason(e.target.value)}/><button disabled={reason.trim().length<5} onClick={review}><BadgeCheck/> Record decision</button></div>}</section>}</div></main>

  const eligible=user?.roles.some(role=>['provider','fleet_owner','driver'].includes(role))
  if(!eligible)return <main className="page"><div className="empty-state"><b>Provider verification is not required</b><p>This customer account does not need a provider KYC application.</p></div></main>
  if(!application){const driver=user?.roles.includes('driver');const fleet=user?.roles.includes('fleet_owner');return <main className="page"><div className="page-title"><span className="kicker">MANUAL VERIFICATION</span><h1>Start provider verification</h1><p>Create the application record now. Secure document upload remains deferred.</p></div>{message&&<div className="privacy-banner">{message}</div>}<form className="panel kyc-create" onSubmit={createApplication}><label>Legal name<input required minLength={2} value={legalName} onChange={e=>setLegalName(e.target.value)}/></label><label>Verification type<select value={providerType} onChange={e=>setProviderType(e.target.value)}>{driver?<option value="driver">Driver</option>:fleet?<><option value="fleet">Fleet owner</option><option value="owner">Vehicle owner</option><option value="company">Company</option></>:<><option value="owner">Vehicle owner</option><option value="company">Company</option></>}</select></label><label>PAN last four characters<input maxLength={4} pattern="[A-Z0-9]{4}" value={pan} onChange={e=>setPan(e.target.value.toUpperCase())}/></label><label>GSTIN (optional)<input maxLength={15} value={gstin} onChange={e=>setGstin(e.target.value.toUpperCase())}/></label><button><ShieldCheck/> Create application</button></form></main>}
  return <main className="page"><div className="page-title"><span className="kicker">MANUAL VERIFICATION</span><h1>Your KYC application</h1><p>{application.legal_name} · {application.provider_type}</p></div>{message&&<div className="privacy-banner">{message}</div>}<section className="panel provider-kyc-live"><div className="kyc-progress-head"><div><span className="badge">{application.status.replaceAll('_',' ')}</span><h2>Verification status</h2><p>{application.decision_reason||'An administrator will review the documents after submission.'}</p></div><strong>{application.documents.length}</strong></div><div className="document-list">{application.documents.map(document=><article key={document.id}><span><FileText/></span><div><b>{labels[document.type]||document.type}</b><small>{document.filename}</small></div><em>{document.status}</em></article>)}{!application.documents.length&&<div className="empty-state"><UploadCloud/><b>Document upload is temporarily unavailable</b><p>Private object storage must be configured before Aadhaar, PAN, licence or RC files can be accepted safely.</p></div>}</div>{['registered','resubmit_required'].includes(application.status)&&<button className="kyc-submit" disabled={!application.documents.length} onClick={submitApplication}><Check/> Submit for review</button>}</section></main>
}
