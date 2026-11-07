export type Endpoint='pickup'|'destination'
export type MapPoint={lat:number;lng:number}
export type LocationFields=Record<string,unknown>
export function locationFromFields(form:LocationFields,end:Endpoint):MapPoint|null{
 const a=form[end+'_lat'],b=form[end+'_lng']
 if(typeof a!=='string'||typeof b!=='string'||!a.trim()||!b.trim()||form[end+'_pin_confirmed']!==true)return null
 const lat=Number(a),lng=Number(b)
 return Number.isFinite(lat)&&Number.isFinite(lng)&&Math.abs(lat)<=90&&Math.abs(lng)<=180?{lat,lng}:null
}
export const clearLocation=(end:Endpoint)=>({[end+'_lat']:'',[end+'_lng']:'',[end+'_pin_confirmed']:true})
export const moveLocation=(end:Endpoint,p:MapPoint)=>({[end+'_lat']:String(p.lat),[end+'_lng']:String(p.lng),[end+'_pin_confirmed']:false})
export const confirmLocation=(end:Endpoint)=>({[end+'_pin_confirmed']:true})
export function pendingLocation(form:LocationFields,end:Endpoint){return locationFromFields({...form,...confirmLocation(end)},end)}
