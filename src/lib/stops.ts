export type StopActivity='pickup'|'drop'|'both'
export type Stop={address:string;activity:StopActivity;note:string}

/** The server accepts up to 20 stops. */
export const MAX_STOPS=20
export const STOP_ACTIVITIES:[StopActivity,string][]=[['pickup','Pick up goods'],['drop','Drop off goods'],['both','Pick up and drop off']]

/** Drafts store every field as text, so the stop list is kept as JSON in one field. */
export function readStops(value:unknown):Stop[]{
  if(typeof value!=='string'||!value)return []
  try{
    const parsed=JSON.parse(value)
    return Array.isArray(parsed)?parsed.filter(item=>item&&typeof item.address==='string').map(item=>({address:item.address,activity:['pickup','drop','both'].includes(item.activity)?item.activity:'drop',note:typeof item.note==='string'?item.note:''})):[]
  }catch{return []}
}

export const writeStops=(stops:Stop[])=>stops.length?JSON.stringify(stops):''

export function stopsPayload(stops:Stop[]){
  return stops.filter(stop=>stop.address.trim()).map(stop=>({address:stop.address.trim(),activity:stop.activity,instructions:stop.note.trim()||null}))
}

export function stopsProblem(stops:Stop[]):string|null{
  const index=stops.findIndex(stop=>stop.address.trim().length>0&&stop.address.trim().length<3)
  return index>=0?`Stop ${index+1} needs a full address.`:null
}
