import React, {useState} from 'react'
import {canOperateTrips} from '../lib/trips'
type Props={roles:string[];status:string;busy:boolean;onIssue:(type:'pickup'|'delivery')=>Promise<void>;onVerify:(type:'pickup'|'delivery',code:string)=>Promise<boolean>}
export default function TripOtpControls({roles,status,busy,onIssue,onVerify}:Props){
  const [code,setCode]=useState('')
  const type=status==='arrived_at_pickup'?'pickup':status==='arrived_at_destination'?'delivery':null
  if(!type)return null
  const issuer=roles.some(role=>['customer','admin','superadmin'].includes(role))
  const verifier=canOperateTrips(roles)
  return <div className="otp-wait"><div><b>{type==='pickup'?'Pickup':'Delivery'} OTP</b><p>Request a code to the booking customer’s mobile. Provider acceptance does not confirm handset delivery.</p></div>
    {issuer&&<button disabled={busy} onClick={()=>void onIssue(type)}>{busy?'Please wait…':`Request ${type} OTP`}</button>}
    {verifier&&<form onSubmit={async event=>{event.preventDefault();if(await onVerify(type,code))setCode('')}}><label>{type==='pickup'?'Pickup':'Delivery'} OTP<input type="text" inputMode="numeric" autoComplete="one-time-code" required pattern="[0-9]{6}" maxLength={6} value={code} onChange={event=>setCode(event.target.value.replace(/\D/g,''))}/></label><button disabled={busy||code.length!==6}>Verify {type} OTP</button></form>}
  </div>
}
