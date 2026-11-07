import {useEffect,useState} from 'react'
import {Check,ShieldCheck} from 'lucide-react'
import {apiFetch,type CurrentUser} from '../lib/api'

type Tone='neutral'|'ok'|'warn'|'bad'
type State={label:string;step:number;tone:Tone;action:string;detail:string}

const STEPS=['Upload PAN','Security scan','Manual review','Verified']

export function verificationState(status:string|null):State{
  switch(status){
    case 'registered':return {label:'Upload your PAN',step:0,tone:'neutral',action:'Continue verification',detail:'Upload a clear photo or PDF of your PAN card to continue.'}
    case 'under_review':return {label:'Under review',step:2,tone:'neutral',action:'View status',detail:'Your PAN passed the security scan. A reviewer is checking it now.'}
    case 'verified':return {label:'Verified',step:4,tone:'ok',action:'View details',detail:'You can publish requirements and book trucks.'}
    case 'resubmit_required':return {label:'Action needed',step:0,tone:'warn',action:'Upload again',detail:'The reviewer needs a clearer or different document.'}
    case 'rejected':return {label:'Not approved',step:2,tone:'bad',action:'View details',detail:'Your verification was not approved. Contact support if you think this is a mistake.'}
    default:return {label:'Not started',step:0,tone:'neutral',action:'Start verification',detail:'We check your PAN once to keep fake bookings off TransivoX. It is never shown to truck owners.'}
  }
}

export function VerificationBox({status,reason,signedIn,onOpen}:{status:string|null;reason:string|null;signedIn:boolean;onOpen:()=>void}){
  const state=verificationState(status)
  return <section className={`verification-box tone-${state.tone}`} aria-labelledby="verification-title">
    <div className="verification-icon" aria-hidden="true">{state.tone==='ok'?<Check/>:<ShieldCheck/>}</div>
    <div className="verification-body">
      <div className="verification-head"><h2 id="verification-title">Verify your account</h2><span className="verification-pill">{state.label}</span></div>
      <p>{state.detail}</p>
      {reason&&state.tone!=='ok'&&<p className="verification-reason"><b>Reviewer note:</b> {reason}</p>}
      <ol className="verification-steps">{STEPS.map((step,index)=><li key={step} className={index<state.step?'done':undefined} aria-current={index===state.step?'step':undefined}><span aria-hidden="true">{index<state.step?<Check/>:index+1}</span>{step}</li>)}</ol>
      <button className={state.tone==='ok'?'secondary':undefined} onClick={onOpen}>{signedIn?state.action:'Sign in to verify'}</button>
    </div>
  </section>
}

/**
 * Uses the app's own sign-in state and asks the server only for a signed-in customer.
 * Never fetches while the session is still being restored: a request then would race the
 * restore's token refresh and could sign the person out.
 */
export default function VerificationCard({user,sessionLoading=false,onOpen,onSignIn,hideWhenVerified=false}:{user:CurrentUser|null;sessionLoading?:boolean;onOpen:()=>void;onSignIn:()=>void;hideWhenVerified?:boolean}){
  const customer=Boolean(user?.roles.includes('customer'))
  const [state,setState]=useState<{status:string|null;reason:string|null}|null>(null)
  useEffect(()=>{
    if(sessionLoading||!customer){setState(null);return}
    let alive=true
    apiFetch<{status:string;decision_reason?:string|null}|null>('/customer-kyc/me')
      .then(item=>{if(alive)setState({status:item?.status||null,reason:item?.decision_reason||null})})
      .catch(()=>{if(alive)setState(null)})
    return()=>{alive=false}},[customer,sessionLoading,user?.id])
  if(sessionLoading)return null
  if(!user)return <VerificationBox status={null} reason={null} signedIn={false} onOpen={onSignIn}/>
  if(!customer||!state||(hideWhenVerified&&state.status==='verified'))return null
  return <VerificationBox {...state} signedIn onOpen={onOpen}/>
}
