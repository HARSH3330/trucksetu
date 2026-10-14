import React,{useState} from 'react'
import {X} from 'lucide-react'
import {apiFetch,publicFetch} from '../lib/api'
import PhoneVerification from './PhoneVerification'

type Mode='request-reset'|'reset'|'verify'|'mobile'
export default function AccountSecurity({close,initialEmail='',initialMode='request-reset',signedIn=false}:{close:()=>void;initialEmail?:string;initialMode?:Mode;signedIn?:boolean}){
  const [mode,setMode]=useState<Mode>(initialMode)
  const [email,setEmail]=useState(initialEmail),[token,setToken]=useState(''),[password,setPassword]=useState(''),[code,setCode]=useState('')
  const [busy,setBusy]=useState(false),[message,setMessage]=useState(''),[error,setError]=useState('')
  const [mobile,setMobile]=useState('')
  const [phoneRevision,setPhoneRevision]=useState(0)
  async function perform(path:string,body:object,success:string){
    setBusy(true);setError('');setMessage('')
    try{await publicFetch(path,{method:'POST',body:JSON.stringify(body)});setMessage(success);return true}
    catch(problem){setError(problem instanceof Error?problem.message:'Account service unavailable.');return false}
    finally{setBusy(false)}
  }
  async function submit(event:React.FormEvent){
    event.preventDefault()
    if(mode==='mobile'){
      if(!signedIn)return
      setBusy(true);setError('');setMessage('')
      try{const result=await apiFetch<{updated:boolean;mobile_verified:boolean}>('/auth/mobile',{method:'PATCH',body:JSON.stringify({mobile,password})});if(result.updated!==true)throw new Error('The server did not confirm the contact update.');setPassword('');setPhoneRevision(value=>value+1);setMessage(result.mobile_verified===true?'Trip contact saved. Existing phone verification retained.':'Trip contact updated. The mobile number is not verified.')}
      catch(problem){setError(problem instanceof Error?problem.message:'Account service unavailable.')}
      finally{setBusy(false)}
    }else if(mode==='request-reset'){
      if(await perform('/auth/password-reset/request',{email},'If your account is eligible and delivery is available, check your inbox. Delivery is not confirmed.'))setMode('reset')
    }else if(mode==='reset'){
      if(await perform('/auth/password-reset/confirm',{email,token,password},'Password updated. Previous sessions are invalidated. Sign in again.')){setToken('');setPassword('')}
    }else if(await perform('/auth/verify-email',{email,code},'Email verified. Close this window and sign in again to refresh account details.'))setCode('')
  }
  function switchMode(next:Mode){setMode(next);setToken('');setPassword('');setCode('');setError('');setMessage('')}
  return <div className="overlay"><div className="modal auth-modal" role="dialog" aria-modal="true" aria-labelledby="account-security-title">
    <button className="modal-close" onClick={close} aria-label="Close account help"><X/></button>
    <div className="wizard-head"><small>ACCOUNT SECURITY</small><h2 id="account-security-title">Account recovery & verification</h2><p>Recover access, verify your email or update your trip contact.</p></div>
    <div className="auth-tabs"><button disabled={busy} onClick={()=>switchMode('request-reset')}>Recover password</button><button disabled={busy} onClick={()=>switchMode('verify')}>Verify email</button>{signedIn&&<button disabled={busy} onClick={()=>switchMode('mobile')}>Trip contact</button>}</div>
    <form className="auth-form" onSubmit={submit}>
      {mode!=='mobile'&&<label>Email address<input type="email" required maxLength={254} value={email} onChange={event=>setEmail(event.target.value)}/></label>}
      {mode==='mobile'&&signedIn&&<><label>Mobile for trip OTP<input type="tel" required pattern="\+?[0-9]{10,15}" maxLength={16} value={mobile} onChange={event=>setMobile(event.target.value)}/></label><label>Current password<input type="password" autoComplete="current-password" required maxLength={72} value={password} onChange={event=>setPassword(event.target.value)}/></label></>}
      {mode==='mobile'&&!signedIn&&<p role="alert">Sign in before changing your trip contact.</p>}
      {mode==='reset'&&<><label>Password reset token<input type="password" name="token" autoComplete="off" required minLength={32} maxLength={128} value={token} onChange={event=>setToken(event.target.value)}/></label><label>New password<input type="password" autoComplete="new-password" required minLength={10} maxLength={72} value={password} onChange={event=>setPassword(event.target.value)}/><small>10–72 characters, including uppercase, lowercase and a number.</small></label></>}
      {mode==='verify'&&<><button type="button" disabled={busy||!email} onClick={()=>void perform('/auth/verification/resend',{email},'If eligible and delivery is available, check your email for a new code. Delivery is not confirmed.')}>Request verification email</button><label>Email verification code<input inputMode="numeric" autoComplete="one-time-code" required pattern="[0-9]{6}" maxLength={6} value={code} onChange={event=>setCode(event.target.value.replace(/\D/g,''))}/></label></>}
      {error&&<div className="form-error" role="alert">{error}</div>}{message&&<p role="status">{message}</p>}
      <button className="auth-submit" disabled={busy||(mode==='mobile'&&!signedIn)}>{busy?'Please wait…':mode==='mobile'?'Save trip contact':mode==='request-reset'?'Request recovery email':mode==='reset'?'Set new password':'Verify email code'}</button>
      {mode==='reset'&&<button type="button" disabled={busy} onClick={()=>switchMode('request-reset')}>Request another recovery email</button>}
    </form>
    {mode==='mobile'&&signedIn&&<PhoneVerification key={phoneRevision}/>}
  </div></div>
}
