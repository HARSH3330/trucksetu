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

/** Repeats the gate next to the Publish button, where the customer actually tries to post. */
export function PublishBlockedNotice({user,kycStatus,onVerify,onAccountHelp}:{user:CurrentUser;kycStatus:string|null|undefined;onVerify?:()=>void;onAccountHelp?:()=>void}){
  const readiness=publishReadiness(user,kycStatus)
  if(readiness.ready||readiness.checking)return null
  const contact=Boolean(user.email_verified||user.mobile_verified)
  const pan=readiness.items.find(item=>item.key==='pan')
  return <div className="verification-box tone-warn publish-blocked" role="alert">
    <div className="verification-body">
      <b>You cannot post this requirement yet.</b>
      <p>Your account must be verified first. Your entries are kept; save a draft and publish once verification is complete.</p>
      <ul className="readiness-list">
        <li className={contact?'done':undefined}>Email or phone: {contact?'verified':'not verified'}</li>
        <li className={pan?.done?'done':undefined}>PAN review: {pan?.done?'verified':pan?.detail.toLowerCase()}</li>
      </ul>
      <div className="demand-actions">
        {!contact&&onAccountHelp&&<button type="button" className="secondary" onClick={onAccountHelp}>Verify email or phone</button>}
        {!pan?.done&&onVerify&&<button type="button" className="secondary" onClick={onVerify}>PAN verification</button>}
      </div>
    </div>
  </div>
}
