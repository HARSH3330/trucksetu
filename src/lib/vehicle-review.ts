export const VEHICLE_DOCUMENT_LABELS:Record<string,string>={rc:'Registration certificate',insurance:'Insurance',fitness:'Fitness certificate',pollution:'Pollution certificate',permit:'Commercial permit'}

type Reviewable={missing_accepted_documents?:string[];awaiting_review_documents?:string[];document_expiries:Record<string,string>}

/** Why the server would refuse approval right now, or null. Mirrors the accepted-document and expiry checks. */
export function approvalBlocker(vehicle:Reviewable,now:Date=new Date()):string|null{
  if(Object.values(vehicle.document_expiries).some(value=>new Date(`${value}T23:59:59`)<now))return 'Renew expired documents before approval.'
  const missing=vehicle.missing_accepted_documents||[]
  if(!missing.length)return null
  const label=(key:string)=>VEHICLE_DOCUMENT_LABELS[key]||key
  const waiting=missing.filter(key=>(vehicle.awaiting_review_documents||[]).includes(key))
  const absent=missing.filter(key=>!waiting.includes(key))
  const parts=[waiting.length&&`Accept these documents under Private document review first: ${waiting.map(label).join(', ')}.`,absent.length&&`Not uploaded yet: ${absent.map(label).join(', ')}.`].filter(Boolean)
  if(!waiting.length)parts.unshift('The truck owner must upload these documents before approval.')
  return parts.join(' ')
}
