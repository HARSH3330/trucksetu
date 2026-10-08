import {useEffect, useRef, useState} from 'react'
import {apiFetch, publicFetch} from '../lib/api'

type Terms = {version:string; content:string; status:string}

export default function TermsConsent({onAccepted,onCancel}:{onAccepted:()=>void;onCancel:()=>void}){
  const [terms,setTerms]=useState<Terms|null>(null)
  const [checked,setChecked]=useState(false)
  const [busy,setBusy]=useState(false)
  const [error,setError]=useState('')
  const closeButton=useRef<HTMLButtonElement>(null)
  useEffect(()=>{closeButton.current?.focus();publicFetch<Terms>('/legal/terms').then(setTerms).catch(()=>setError('Unable to load Terms. Close this window and try again.'))},[])
  async function accept(){
    if(!checked||!terms||busy)return
    setBusy(true);setError('')
    try{await apiFetch('/legal/terms/acceptance',{method:'POST',body:JSON.stringify({version:terms.version,accepted:true})});onAccepted()}
    catch(error){setError(error instanceof Error?error.message:'Unable to save acceptance');setBusy(false)}
  }
  return <div className="overlay"><section className="modal" role="dialog" aria-modal="true" aria-labelledby="terms-title" onKeyDown={event=>{
    if(event.key==='Escape'&&!busy)onCancel()
    if(event.key==='Tab'){
      const controls=Array.from(event.currentTarget.querySelectorAll<HTMLElement>('button:not(:disabled),input:not(:disabled),[tabindex="0"]'))
      const first=controls[0],last=controls.at(-1)
      if(event.shiftKey&&document.activeElement===first){event.preventDefault();last?.focus()}
      else if(!event.shiftKey&&document.activeElement===last){event.preventDefault();first?.focus()}
    }
  }}>
    <button ref={closeButton} className="modal-close" disabled={busy} onClick={onCancel} aria-label="Close Terms">×</button>
    <h2 id="terms-title">Terms & Conditions</h2>
    <p>Review and accept before your first booking. We will ask again when the Terms change.</p>
    {terms?<><small>Version {terms.version} · Draft pending legal review</small><div tabIndex={0} aria-label="Full Terms and Conditions" style={{maxHeight:'45vh',overflow:'auto',whiteSpace:'pre-wrap',padding:'16px',border:'1px solid #dce6e2',borderRadius:8,margin:'16px 0',fontSize:13}}>{terms.content}</div>
    <label className="check"><input type="checkbox" checked={checked} disabled={busy} onChange={event=>setChecked(event.target.checked)}/>I have read and accept the Terms & Conditions shown above.</label></>:!error&&<p role="status">Loading Terms…</p>}
    {error&&<p className="form-error" role="alert">{error}</p>}
    <div className="wizard-foot" style={{marginTop:20}}><button className="secondary" disabled={busy} onClick={onCancel}>Cancel</button><button className="auth-submit" disabled={!terms||!checked||busy} onClick={accept}>{busy?'Saving acceptance…':'Accept and continue'}</button></div>
  </section></div>
}
