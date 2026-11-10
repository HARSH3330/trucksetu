import {useEffect,useRef,useState} from 'react'
import {publicFetch,saveSession,sessionFetch,type CurrentUser} from '../lib/api'
import {PRIVACY_VERSION} from '../lib/privacy-notice'
import SignupConsent from './SignupConsent'
import {PhoneField,ROLE_CHOICES} from './SignupHelp'

type GoogleApi={accounts:{id:{initialize:(o:object)=>void;renderButton:(el:HTMLElement,o:object)=>void}}}
type Session={access_token:string;user:CurrentUser}
type GoogleResult=({status:'signed_in'}&Session)|{status:'role_required';email:string;name:string}

let script:Promise<GoogleApi>|null=null
function loadGoogle():Promise<GoogleApi>{
  const ready=(window as unknown as {google?:GoogleApi}).google
  if(ready?.accounts?.id)return Promise.resolve(ready)
  script??=new Promise((resolve,reject)=>{
    const tag=document.createElement('script');tag.src='https://accounts.google.com/gsi/client';tag.async=true
    tag.onload=()=>{const api=(window as unknown as {google?:GoogleApi}).google;if(api?.accounts?.id)resolve(api);else reject(new Error('unavailable'))}
    tag.onerror=()=>{script=null;reject(new Error('unavailable'))};document.head.append(tag)
  })
  return script
}

/** Shown when a Google account is new to TransivoX: pick a role and agree before the account is created. */
export function GoogleRoleStep({email,role,mobile,agreed,busy,onRole,onMobile,onAgree,onCreate,onCancel}:{email:string;role:string;mobile:string;agreed:boolean;busy:boolean;onRole:(role:string)=>void;onMobile:(value:string)=>void;onAgree:(value:boolean)=>void;onCreate:()=>void;onCancel:()=>void}){
  return <form className="google-role-step" onSubmit={event=>{event.preventDefault();onCreate()}}>
    <h3>Finish creating your account</h3>
    <p>Signing up as <b>{email}</b> with Google.</p>
    <label>I’m joining as<select value={role} onChange={event=>onRole(event.target.value)}>{ROLE_CHOICES.map(choice=><option key={choice.value} value={choice.value}>{choice.label}</option>)}</select><small className="role-help">{ROLE_CHOICES.find(choice=>choice.value===role)?.help}</small></label>
    <PhoneField role={role} value={mobile} onChange={onMobile}/>
    <SignupConsent checked={agreed} onChange={onAgree}/>
    <button className="auth-submit" disabled={busy||!agreed}>{busy?'Creating account…':'Create account'}</button>
    <button type="button" className="secondary" disabled={busy} onClick={onCancel}>Use another way</button>
  </form>
}

export default function GoogleSignIn({signedIn}:{signedIn:(user:CurrentUser)=>void}){
  const holder=useRef<HTMLDivElement>(null)
  const [available,setAvailable]=useState(false),[error,setError]=useState(''),[busy,setBusy]=useState(false)
  const [pending,setPending]=useState<{credential:string;email:string}|null>(null),[role,setRole]=useState('customer'),[mobile,setMobile]=useState(''),[agreed,setAgreed]=useState(false)
  const latest=useRef(signedIn);latest.current=signedIn

  async function send(body:object){
    setBusy(true);setError('')
    try{
      const result=await sessionFetch<GoogleResult>('google',{method:'POST',body:JSON.stringify(body)})
      if(result.status==='role_required'){setPending({credential:(body as {credential:string}).credential,email:result.email});return}
      saveSession(result);latest.current(result.user)
    }catch(failure){setError(failure instanceof Error?failure.message:'Google sign-in did not work. Try again or use your email.')}
    finally{setBusy(false)}
  }

  useEffect(()=>{let alive=true
    publicFetch<{enabled:boolean;client_id:string|null}>('/auth/google/config').then(async config=>{
      if(!alive||!config.enabled||!config.client_id)return
      const google=await loadGoogle();if(!alive||!holder.current)return
      google.accounts.id.initialize({client_id:config.client_id,ux_mode:'popup',auto_select:false,cancel_on_tap_outside:true,callback:(response:{credential?:string})=>{if(response.credential)void send({credential:response.credential})}})
      google.accounts.id.renderButton(holder.current,{theme:'outline',size:'large',text:'continue_with',shape:'rectangular',logo_alignment:'left',width:Math.min(380,holder.current.clientWidth||320)})
      setAvailable(true)
    }).catch(()=>{if(alive)setAvailable(false)})
    return()=>{alive=false}},[])

  if(pending)return <GoogleRoleStep email={pending.email} role={role} mobile={mobile} agreed={agreed} busy={busy} onRole={setRole} onMobile={setMobile} onAgree={setAgreed}
    onCreate={()=>void send({credential:pending.credential,role,mobile:mobile.trim()||null,privacy_notice_version:PRIVACY_VERSION})} onCancel={()=>{setPending(null);setAgreed(false)}}/>
  return <div className="google-signin" hidden={!available&&!error}>
    <div ref={holder} className="google-button" aria-label="Continue with Google"/>
    {error&&<p className="form-error" role="alert">{error}</p>}
    {available&&<p className="auth-divider"><span>or use your email</span></p>}
  </div>
}
