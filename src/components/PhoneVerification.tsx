import {useEffect,useRef,useState} from 'react'
import {apiFetch,ApiError,type CurrentUser} from '../lib/api'
import {loadMsg91Widget,widgetIdentifier,widgetToken} from '../lib/msg91-widget'

let widgetOwner:symbol|null=null

export default function PhoneVerification(){
  const [profile,setProfile]=useState<CurrentUser|null>(null),[state,setState]=useState('loading')
  const [busy,setBusy]=useState(false),[message,setMessage]=useState(''),[error,setError]=useState('')
  const generation=useRef(0),mounted=useRef(false)
  const owner=useRef(Symbol('phone verification'))
  const widgetId=import.meta.env.VITE_MSG91_WIDGET_ID||'',tokenAuth=import.meta.env.VITE_MSG91_WIDGET_TOKEN_AUTH||''
  async function load(){
    setState('loading')
    try{const current=await apiFetch<CurrentUser>('/auth/me');if(mounted.current){setProfile(current);setState('ready')}}
    catch(problem){if(mounted.current)setState(problem instanceof ApiError&&[401,403].includes(problem.status)?'signed-out':'error')}
  }
  useEffect(()=>{
    mounted.current=true;void load()
    return ()=>{mounted.current=false;generation.current++;if(widgetOwner===owner.current)document.querySelector('msg91-otp-provider')?.remove();setTimeout(()=>{if(!mounted.current&&widgetOwner===owner.current)document.querySelector('msg91-otp-provider')?.remove()},50)}
  },[])
  async function start(){
    if(busy||!profile?.mobile||!widgetId||!tokenAuth)return
    const run=++generation.current
    widgetOwner=owner.current
    const current=()=>mounted.current&&run===generation.current&&widgetOwner===owner.current
    setBusy(true);setError('');setMessage('Opening phone verification. Completion requires server validation.')
    try{
      const initialise=await loadMsg91Widget();if(!current())return
      let submitting=false
      initialise({widgetId,tokenAuth,identifier:widgetIdentifier(profile.mobile),exposeMethods:false,
        success:async data=>{
          if(!current()||submitting)return
          const token=widgetToken(data)
          if(!token){setBusy(false);setError('The widget did not return a usable verification proof. Start again.');return}
          submitting=true;setMessage('Validating the phone proof with the server…')
          try{const result=await apiFetch<{mobile_verified:boolean}>('/auth/mobile/verify-widget',{method:'POST',body:JSON.stringify({verification_token:token})});if(result.mobile_verified!==true)throw new Error('The server did not confirm phone verification.');if(current()){setMessage('Phone verified. Provider verification is a separate process.');await load()}}
          catch(problem){if(current()){setMessage('');setError(problem instanceof Error?problem.message:'Phone verification failed.')}}
          finally{if(current())setBusy(false)}
        },
        failure:()=>{if(current()&&!submitting){setBusy(false);setMessage('');setError('Phone verification was not completed. You can try again.')}}
      })
    }catch{if(current()){setBusy(false);setMessage('');setError('Phone verification widget could not be loaded. Check your connection or try again.')}}
  }
  function cancel(){const marker=++generation.current;setBusy(false);setMessage('Verification cancelled; the phone was not marked verified by this action.');if(widgetOwner===owner.current)document.querySelector('msg91-otp-provider')?.remove();setTimeout(()=>{if(generation.current===marker&&widgetOwner===owner.current)document.querySelector('msg91-otp-provider')?.remove()},50)}
  return <section aria-label="Phone ownership verification"><h3>Verify saved phone</h3>
    {state==='loading'&&<p role="status">Loading phone verification status…</p>}{state==='error'&&<button type="button" onClick={load}>Retry phone status</button>}{state==='signed-out'&&<p role="alert">Sign in to verify your phone.</p>}
    {state==='ready'&&<><p>{profile?.mobile?`${profile.mobile} · ${profile.mobile_verified?'verified':'not verified'}`:'Save a mobile number above before verifying it.'}</p>{(!widgetId||!tokenAuth)&&<p>Phone verification is currently unavailable. You can still sign in with your email and password.</p>}<button type="button" disabled={busy||!profile?.mobile||Boolean(profile.mobile_verified)||!widgetId||!tokenAuth} onClick={()=>void start()}>Verify saved phone (send OTP)</button></>}
    {busy&&<button type="button" onClick={cancel}>Cancel phone verification</button>}{message&&<p role="status">{message}</p>}{error&&<p role="alert">{error}</p>}
  </section>
}
