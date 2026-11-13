import {Check,ShieldCheck} from 'lucide-react'
import type {CurrentUser} from '../lib/api'
import {publishReadiness} from '../lib/publish-readiness'

/** Tells a customer, before they fill in a requirement, exactly which verification steps still block publishing. */
export default function PublishReadiness({user,kycStatus,onVerify,onAccountHelp}:{user:CurrentUser;kycStatus:string|null|undefined;onVerify?:()=>void;onAccountHelp?:()=>void}){
  const readiness=publishReadiness(user,kycStatus)
  if(readiness.ready)return null
  return <section className={`verification-box ${readiness.checking?'tone-neutral':'tone-warn'} publish-readiness`} aria-labelledby="publish-readiness-title" aria-busy={readiness.checking}>
    <div className="verification-icon" aria-hidden="true"><ShieldCheck/></div>
    <div className="verification-body">
      <h2 id="publish-readiness-title">Before you can publish</h2>
      <p>{readiness.summary} You can still save this requirement as a draft.</p>
      <ul className="readiness-list">{readiness.items.map(item=><li key={item.key} className={item.done?'done':undefined}><span aria-hidden="true">{item.done?<Check/>:'•'}</span><div><b>{item.label}:</b> {item.detail}</div></li>)}</ul>
      <div className="demand-actions">
        {!readiness.items.some(item=>item.key!=='pan'&&item.done)&&onAccountHelp&&<button type="button" className="secondary" onClick={onAccountHelp}>Verify email or phone</button>}
        {!readiness.checking&&kycStatus!=='verified'&&onVerify&&<button type="button" className="secondary" onClick={onVerify}>PAN verification</button>}
      </div>
    </div>
  </section>
}
