import {useEffect, useMemo, useState} from 'react'
import {AlertTriangle, BadgeCheck, Check, FileText, ShieldCheck, UploadCloud, X} from 'lucide-react'
import {ApiError, apiFetch, type CurrentUser} from '../lib/api'
import './LiveKYC.css'
import {KYC_DOCUMENT_LABELS,kycStatusLabel,missingDocuments,providerTypeLabel,requiredDocumentKeys} from '../lib/kyc-requirements'

type Document={id:string;type:string;filename:string;status:string;expires_on:string|null}
type Application={id:string;provider_id:string;provider_name:string|null;provider_type:string|null;status:string;legal_name:string;submitted_at:string|null;decision_reason:string|null;documents:Document[]}
type Expiring={id:string;type:string;expires_on:string;status:string}
const labels=KYC_DOCUMENT_LABELS
const allowed:Record<string,string[]>={driver:['aadhaar','pan','driving_licence','bank_proof'],owner:['aadhaar','pan','driving_licence','vehicle_rc','vehicle_insurance','fitness_certificate','commercial_permit','pollution_certificate','bank_proof'],fleet:Object.keys(labels),company:Object.keys(labels)}
/** Verification types each role may submit, matching the server's check; the first is preselected. */
export function verificationTypes(roles:string[]):{initial:string;options:[string,string][]}{
  const options:[string,string][]=roles.includes('driver')?[['driver','Driver']]:roles.includes('fleet_owner')?[['fleet','Fleet owner'],['owner','Vehicle owner'],['company','Company']]:[['owner','Vehicle owner'],['company','Company']]
  return {initial:options[0][0],options}
}
type PendingUpload={document_type:string;storage_key:string;original_filename:string;content_type:string;expires_on:string|null}

export default function LiveKYC({embedded=false}:{embedded?:boolean}={}){
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
  const [uploadType,setUploadType]=useState('')
  const [uploadFile,setUploadFile]=useState<File|null>(null)
  const [uploadExpiry,setUploadExpiry]=useState('')
  const [pendingUpload,setPendingUpload]=useState<PendingUpload|null>(null)
  const [uploadBusy,setUploadBusy]=useState(false)
  const [actionBusy,setActionBusy]=useState(false)

  const admin=Boolean(user?.roles.some(role=>['admin','superadmin'].includes(role)))
  const current=useMemo(()=>queue.find(item=>item.id===selected)||queue[0]||null,[queue,selected])

  async function loadQueue(statusValue=filter){
    const [items,expiry]=await Promise.all([apiFetch<Application[]>(`/kyc/admin/applications?status=${statusValue}`),apiFetch<Expiring[]>('/kyc/admin/expiring-documents?days=30')])
    setQueue(items);setExpiring(expiry);setSelected(items[0]?.id||'')
  }
  async function load(){
    setState('loading')
    try{
      const profile=await apiFetch<CurrentUser>('/auth/me');setUser(profile);setProviderType(verificationTypes(profile.roles).initial)
      if(profile.roles.some(role=>['admin','superadmin'].includes(role)))await loadQueue()
      else{try{setApplication(await apiFetch<Application>('/kyc/applications/me'))}catch(error){if(!(error instanceof ApiError&&error.status===404))throw error}}
      setState('ready')
    }catch(error){setState(error instanceof ApiError&&error.status===401?'signed-out':'error')}
  }
  useEffect(()=>{void load()},[])
  useEffect(()=>{if(current){setDecision(current.status==='suspended'?'resubmit_required':'verified');setDocumentDecisions(Object.fromEntries(current.documents.map(document=>[document.type,'accepted'])))}else setDocumentDecisions({})},[current])

  async function createApplication(event:React.FormEvent){
    event.preventDefault();if(actionBusy)return;setActionBusy(true);setMessage('Creating verification application…')
    try{setApplication(await apiFetch<Application>('/kyc/applications',{method:'POST',body:JSON.stringify({legal_name:legalName,provider_type:providerType,pan_last_four:pan||null,gstin:gstin||null})}));setMessage('Application created. Upload the required documents below.')}
    catch(error){setMessage(error instanceof Error?error.message:'Application could not be created')}
    finally{setActionBusy(false)}
  }
  async function submitApplication(){
    if(!application||actionBusy)return
    setActionBusy(true)
    try{setApplication(await apiFetch<Application>(`/kyc/applications/${application.id}/submit`,{method:'POST'}));setMessage('Application submitted for manual review.')}
    catch(error){setMessage(error instanceof Error?error.message:'Application could not be submitted')}
    finally{setActionBusy(false)}
  }
  async function review(){
    if(!current||actionBusy)return
    if(['rejected','suspended'].includes(decision)&&!window.confirm(`Record ${decision} for this provider? The reason will remain in the review history.`))return
    setActionBusy(true)
    setMessage('Recording review…')
    try{await apiFetch(`/kyc/admin/applications/${current.id}/review`,{method:'POST',body:JSON.stringify({decision,reason,document_decisions:documentDecisions})});await loadQueue();setMessage('Review decision recorded.')}
    catch(error){setMessage(error instanceof Error?error.message:'Review could not be recorded')}
    finally{setActionBusy(false)}
  }

  async function completeDocument(payload:PendingUpload){
    try{
      await apiFetch('/kyc/documents',{method:'POST',body:JSON.stringify(payload)})
      setPendingUpload(null);setUploadFile(null);setUploadExpiry('');setMessage('Document uploaded and passed the safety check.');await load()
    }catch(error){
      if(error instanceof ApiError&&error.status===409&&error.message.includes('scan')){setPendingUpload(payload);setMessage('Upload received. We are still running a safety check on the file; select Check again in a minute.')}
      else setMessage(error instanceof Error?error.message:'Document registration failed')
    }
  }
  async function uploadDocument(event:React.FormEvent){
    event.preventDefault()
    if(!uploadFile||!uploadType||uploadBusy)return
    if(uploadFile.size===0||uploadFile.size>10*1024*1024){setMessage('Choose a file between 1 byte and 10 MB.');return}
    const contentType=uploadFile.type
    if(!['application/pdf','image/jpeg','image/png'].includes(contentType)){setMessage('Only PDF, JPEG and PNG documents are accepted.');return}
    setUploadBusy(true);setMessage('Preparing a private upload…')
    try{
      const prepared=await apiFetch<{storage_key:string;upload_url:string}>('/kyc/uploads',{method:'POST',body:JSON.stringify({document_type:uploadType,filename:uploadFile.name,content_type:contentType})})
      const uploaded=await fetch(prepared.upload_url,{method:'PUT',headers:{'Content-Type':contentType,'x-amz-server-side-encryption':'AES256'},body:uploadFile})
      if(!uploaded.ok)throw new Error('Upload failed. Check your connection and try again.')
      setMessage('Upload complete. Running a safety check on the file…')
      await completeDocument({document_type:uploadType,storage_key:prepared.storage_key,original_filename:uploadFile.name,content_type:contentType,expires_on:uploadExpiry||null})
    }catch(error){setMessage(error instanceof Error?error.message:'Document upload failed')}
    finally{setUploadBusy(false)}
  }
  async function viewDocument(id:string){
    try{
      const result=await apiFetch<{download_url:string}>(`/kyc/documents/${id}/download`)
      window.open(result.download_url,'_blank','noopener,noreferrer')
    }catch(error){setMessage(error instanceof Error?error.message:'Document cannot be opened')}
  }

  const wrap=(content:React.ReactNode)=>embedded?<section className="panel provider-review">{content}</section>:<main className="page">{content}</main>
  if(state==='loading')return wrap(<div className="empty-state">Loading verification workspace…</div>)
  if(state==='signed-out')return wrap(<div className="empty-state"><b>Sign in required</b><p>Verification records are private.</p></div>)
  if(state==='error')return wrap(<div className="empty-state"><b>Verification workspace unavailable</b><button onClick={load}>Retry</button></div>)
  if(admin){const body=<>{message&&<div className="privacy-banner" role="status">{message}</div>}<div className="kyc-summary"><span><b>{queue.length}</b><small>{filter.replaceAll('_',' ')}</small></span><span><b>{expiring.filter(x=>x.status==='expired').length}</b><small>Expired documents</small></span><span><b>{expiring.filter(x=>x.status==='expiring').length}</b><small>Expiring within 30 days</small></span></div><div className="kyc-filter"><select aria-label="Application status filter" disabled={actionBusy} value={filter} onChange={async e=>{setFilter(e.target.value);try{await loadQueue(e.target.value)}catch{setState('error')}}}><option value="under_review">Under review</option><option value="verified">Verified</option><option value="resubmit_required">Resubmission required</option><option value="rejected">Rejected</option><option value="suspended">Suspended</option></select></div><div className="kyc-admin-grid"><aside className="kyc-queue">{queue.map(item=><button className={current?.id===item.id?'active':''} onClick={()=>setSelected(item.id)} key={item.id}><span>{(item.provider_name||item.legal_name).split(' ').map(x=>x[0]).join('').slice(0,2)}</span><div><b>{item.provider_name||item.legal_name}</b><small>{providerTypeLabel(item.provider_type)} · {item.documents.length} documents</small><em>{item.submitted_at?new Date(item.submitted_at).toLocaleString('en-IN'):'Not submitted'}</em></div></button>)}{!queue.length&&<div className="empty-state">No applications in this queue.</div>}</aside>{current&&<section className="panel kyc-review"><div className="panel-head"><div><span className="badge">{kycStatusLabel(current.status)}</span><h2>{current.legal_name}</h2><p>{providerTypeLabel(current.provider_type)} · {current.provider_name}</p></div></div><div className="kyc-risk"><AlertTriangle/><span><b>Document review</b><small>Review the actual clean-scanned document before accepting it.</small></span></div><div className="document-list">{current.documents.map(document=><article key={document.id}><span><FileText/></span><div><b>{labels[document.type]||document.type}</b><small>{document.filename}</small></div><em>{document.expires_on||'No expiry'}</em><button type="button" onClick={()=>viewDocument(document.id)}>View file</button><select aria-label={`Decision for ${labels[document.type]||document.type}`} disabled={actionBusy} value={documentDecisions[document.type]||'accepted'} onChange={e=>setDocumentDecisions({...documentDecisions,[document.type]:e.target.value as 'accepted'|'rejected'})}><option value="accepted">Accept</option><option value="rejected">Reject</option></select></article>)}{!current.documents.length&&<div className="empty-state">No documents registered.</div>}</div>{['under_review','verified','suspended'].includes(current.status)&&<div className="review-form"><select aria-label="Application decision" disabled={actionBusy} value={decision} onChange={e=>setDecision(e.target.value)}><option value="verified" disabled={current.status==='suspended'}>Verify</option><option value="resubmit_required">Request resubmission</option><option value="rejected" disabled={current.status==='suspended'}>Reject</option><option value="suspended" disabled={current.status==='suspended'}>Suspend</option></select><textarea aria-label="Review reason" disabled={actionBusy} minLength={5} value={reason} onChange={e=>setReason(e.target.value)}/><button disabled={actionBusy||reason.trim().length<5} onClick={review}><BadgeCheck/> Record decision</button></div>}</section>}</div></>
    return embedded?<section className="panel provider-review" aria-labelledby="provider-review-title"><h2 id="provider-review-title">Truck owner and driver documents</h2>{body}</section>:<main className="page"><div className="page-title"><span className="kicker">MANUAL ADMIN VERIFICATION</span><h1>Verification review queue</h1><p>View each document and record a decision with a review reason. Only scan-clean files are available for review.</p></div>{body}</main>}

  const eligible=user?.roles.some(role=>['provider','fleet_owner','driver'].includes(role))
  if(!eligible)return <main className="page"><div className="empty-state"><b>Provider verification is not required</b><p>This customer account does not need a provider KYC application.</p></div></main>
  if(!application){return<main className="page"><div className="page-title"><span className="kicker">MANUAL VERIFICATION</span><h1>Start provider verification</h1><p>Create your application, then upload the required documents. Files stay private and are seen only by the TransivoX review team.</p></div>{message&&<div className="privacy-banner" role="status">{message}</div>}<form className="panel kyc-create" onSubmit={createApplication}><label>Legal name<input required minLength={2} value={legalName} onChange={e=>setLegalName(e.target.value)}/></label><label>Verification type<select value={providerType} onChange={e=>setProviderType(e.target.value)}>{verificationTypes(user?.roles||[]).options.map(([value,label])=><option key={value} value={value}>{label}</option>)}</select></label><p className="kyc-required" role="note">You will need to upload: <b>{requiredDocumentKeys(providerType).map(key=>labels[key]).join(', ')}</b>.</p><label>PAN last four characters<input maxLength={4} pattern="[A-Z0-9]{4}" value={pan} onChange={e=>setPan(e.target.value.toUpperCase())}/></label><label>GSTIN{requiredDocumentKeys(providerType).includes('gst_certificate')?'':' (optional)'}<input maxLength={15} value={gstin} onChange={e=>setGstin(e.target.value.toUpperCase())}/></label><button disabled={actionBusy}><ShieldCheck/> {actionBusy?'Creating…':'Create application'}</button></form></main>}
  return <main className="page"><div className="page-title"><span className="kicker">MANUAL VERIFICATION</span><h1>Your KYC application</h1><p>{application.legal_name} · {providerTypeLabel(application.provider_type)}</p></div>{message&&<div className="privacy-banner" role="status">{message}</div>}<section className="panel provider-kyc-live"><div className="kyc-progress-head"><div><span className="badge">{kycStatusLabel(application.status)}</span><h2>Verification status</h2><p>{application.decision_reason||'An administrator will review the documents after submission.'}</p></div><strong>{application.documents.length}</strong></div><div className="document-list">{application.documents.map(document=><article key={document.id}><span><FileText/></span><div><b>{labels[document.type]||document.type}</b><small>{document.filename}</small></div><em>{kycStatusLabel(document.status)}</em></article>)}{!application.documents.length&&<div className="empty-state"><UploadCloud/><b>No documents uploaded yet</b><p>Use the private upload form below.</p></div>}</div><div className="kyc-required" aria-label="Required documents"><b>Required for {providerTypeLabel(application.provider_type).toLowerCase()} verification</b><ul>{requiredDocumentKeys(application.provider_type).map(key=>{const done=application.documents.some(item=>item.type===key&&item.status!=='rejected');return <li key={key}>{done?<Check aria-hidden/>:<X aria-hidden/>} {labels[key]} — {done?'uploaded':'still needed'}</li>})}</ul></div>{['registered','resubmit_required'].includes(application.status)&&<><form className="kyc-upload" onSubmit={uploadDocument}><h3>Upload a private document</h3><p>PDF, JPEG or PNG · maximum 10 MB. Each file gets an automatic safety check before it is saved.</p><label>Document type<select required value={uploadType} onChange={e=>setUploadType(e.target.value)}><option value="">Select document</option>{(allowed[application.provider_type||'']||[]).filter(type=>!application.documents.some(item=>item.type===type&&item.status!=='rejected')).map(type=><option value={type} key={type}>{labels[type]||type}</option>)}</select></label><label>File<input required type="file" accept=".pdf,.jpg,.jpeg,.png,application/pdf,image/jpeg,image/png" onChange={e=>setUploadFile(e.target.files?.[0]||null)}/></label><label>Expiry date, if applicable<input type="date" value={uploadExpiry} onChange={e=>setUploadExpiry(e.target.value)}/></label><button disabled={uploadBusy||!uploadType||!uploadFile}>{uploadBusy?'Uploading…':'Upload securely'}</button></form>{pendingUpload&&<button className="kyc-scan-retry" disabled={uploadBusy} onClick={()=>void completeDocument(pendingUpload)}>Check again</button>}</>}{['registered','resubmit_required'].includes(application.status)&&<>{missingDocuments(application.provider_type,application.documents).length>0&&<p className="kyc-submit-hint" id="kyc-submit-hint">Upload {missingDocuments(application.provider_type,application.documents).join(', ')} to submit.</p>}<button className="kyc-submit" aria-describedby={missingDocuments(application.provider_type,application.documents).length?'kyc-submit-hint':undefined} disabled={actionBusy||uploadBusy||missingDocuments(application.provider_type,application.documents).length>0} onClick={submitApplication}><Check/> Submit for review</button></>}</section></main>
}
