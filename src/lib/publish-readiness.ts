import type {CurrentUser} from './api'

export type ReadinessItem={key:'email'|'phone'|'pan';label:string;done:boolean;detail:string}
export type Readiness={ready:boolean;checking:boolean;items:ReadinessItem[];summary:string}

/** Mirrors the server's publish gate: a verified email OR phone, plus an approved PAN review.
 *  `kycStatus` is undefined while the status is still being loaded. */
export function publishReadiness(user:Pick<CurrentUser,'email'|'email_verified'|'mobile'|'mobile_verified'>|null,kycStatus:string|null|undefined):Readiness{
  const email=Boolean(user?.email_verified),phone=Boolean(user?.mobile_verified)
  const contact=email||phone
  const items:ReadinessItem[]=[
    {key:'email',label:'Email address',done:email,detail:email?'Verified':contact?'Not verified (optional, your phone is verified)':user?.email?`Enter the code we email to ${user.email}`:'Add and verify an email address'},
    {key:'phone',label:'Phone number',done:phone,detail:phone?'Verified':contact?'Not verified (optional, your email is verified)':user?.mobile?`Confirm the SMS code sent to ${user.mobile}`:'Add a phone number, then confirm the SMS code'},
    {key:'pan',label:'PAN review',done:kycStatus==='verified',detail:kycStatus===undefined?'Checking…':panDetail(kycStatus)},
  ]
  const checking=kycStatus===undefined
  const ready=contact&&kycStatus==='verified'
  const missing=[!contact&&'verify your email or phone (one is enough)',kycStatus!=='verified'&&!checking&&'complete the PAN review'].filter(Boolean)
  return {ready,checking,items,summary:ready?'Your account can publish requirements.':checking?'Checking your verification status…':`You cannot publish until you ${missing.join(' and ')}.`}
}

function panDetail(status:string|null):string{
  switch(status){
    case 'verified':return 'Verified'
    case 'under_review':return 'Uploaded; a reviewer is checking it'
    case 'registered':return 'Started; upload your PAN to continue'
    case 'resubmit_required':return 'Upload again; the reviewer needs a clearer document'
    case 'rejected':return 'Not approved; contact support if you think this is a mistake'
    default:return 'Not started'
  }
}
