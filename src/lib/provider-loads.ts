import type {Demand,DemandBid,Selection} from './demand-types'

export type ProviderProfile={id:string;display_name?:string;provider_type?:string;kyc_status:string;active:boolean}
export type Vehicle={id:string;registration_number:string;maximum_payload_tonnes:string;maximum_volume_m3:string;status:string;document_eligible_today:boolean}
export type Driver={id:string;full_name:string;active:boolean;kyc_status:string;contact_ready?:boolean}
export type ProviderWorkspace={demands:Demand[];profile:ProviderProfile|null;canBid:boolean;bids:DemandBid[];selections:Selection[];vehicles:Vehicle[];drivers:Driver[];unavailable:string[]}
type Fetch=<T>(path:string)=>Promise<T>

/** Open requirements load first and alone decide whether the workspace renders; every other section is optional.
 *  A truck owner without a verified profile is expected to lack bids, trucks and drivers, so those failures are not reported. */
export async function loadProviderWorkspace(fetch:Fetch,filter:URLSearchParams):Promise<ProviderWorkspace>{
  const demands=await fetch<Demand[]>(`/demands?${filter}`)
  const profile=await fetch<ProviderProfile>('/providers/me').catch(()=>null)
  const canBid=Boolean(profile&&profile.active&&profile.kyc_status==='verified')
  const unavailable:string[]=[]
  const optional=async<T>(label:string,path:string|null,fallback:T):Promise<T>=>{
    if(!path)return fallback
    try{return await fetch<T>(path)}catch{if(canBid)unavailable.push(label);return fallback}
  }
  const [bids,selections,vehicles,drivers]=await Promise.all([
    optional<DemandBid[]>('your bids','/demand-bids/mine',[]),
    optional<Selection[]>('won jobs','/demand-selections/mine',[]),
    optional<Vehicle[]>('your trucks','/carrier-vehicles',[]),
    optional<Driver[]>('your drivers',profile?`/providers/${profile.id}/drivers`:null,[]),
  ])
  return {demands,profile,canBid,bids,selections,vehicles,drivers,unavailable}
}

export function bidGateMessage(profile:ProviderProfile|null):string|null{
  if(!profile)return 'You can read open requirements now. Create your provider profile and complete verification to bid.'
  if(!profile.active)return 'Your provider account is inactive, so bidding is unavailable. Contact support.'
  if(profile.kyc_status==='verified')return null
  const status=profile.kyc_status.replaceAll('_',' ')
  return `You can read open requirements now. Bidding opens once your provider verification is approved (currently: ${status}).`
}

/** Says up front when no truck can carry a bid yet. `loaded` is false when the truck list failed to load, so nothing is claimed. */
export function truckGateMessage(trucks:{status:string;document_eligible_today:boolean}[],loaded:boolean):string|null{
  if(!loaded)return null
  if(!trucks.length)return 'Add a truck and upload its documents before you bid. Our team reviews each truck; you can bid once one is approved.'
  if(trucks.some(truck=>truck.status==='approved'&&truck.document_eligible_today))return null
  return `Your ${trucks.length>1?'trucks are':'truck is'} waiting for review. You can bid once our team approves ${trucks.length>1?'one':'it'} and accepts its documents.`
}

/** Mirrors the server's contact rule for bidding: a phone number plus a verified email or phone. */
export function contactGateMessage(user:{mobile?:string|null;email_verified?:boolean;mobile_verified?:boolean}):string|null{
  if(!user.mobile)return 'Add a phone number to your account before you bid. Customers get this number after they pay.'
  if(!user.email_verified&&!user.mobile_verified)return 'Verify your email or phone before you bid.'
  return null
}

/** Mirrors the server's assignment rule so ineligible drivers are explained, not silently offered. */
export function driverChoice(driver:Driver):{eligible:boolean;reason:string}{
  if(!driver.active)return {eligible:false,reason:'inactive'}
  if(driver.kyc_status!=='verified')return {eligible:false,reason:'verification not approved'}
  if(driver.contact_ready===false)return {eligible:false,reason:'needs a verified email or phone'}
  return {eligible:true,reason:''}
}
