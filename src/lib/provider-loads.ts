import type {Demand,DemandBid,Selection} from './demand-types'

export type ProviderProfile={id:string;display_name?:string;provider_type?:string;kyc_status:string;active:boolean}
export type Vehicle={id:string;registration_number:string;maximum_payload_tonnes:string;maximum_volume_m3:string;status:string;document_eligible_today:boolean}
export type Driver={id:string;full_name:string;active:boolean;kyc_status:string}
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
