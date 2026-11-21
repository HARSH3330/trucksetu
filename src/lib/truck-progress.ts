const DOCUMENTS:Record<string,string>={rc:'the registration certificate (RC)',insurance:'the insurance',fitness:'the fitness certificate',pollution:'the pollution certificate',permit:'the permit'}
const LABELS:Record<string,string>={rc:'Registration certificate (RC)',insurance:'Insurance',fitness:'Fitness certificate',pollution:'Pollution certificate (PUC)',permit:'Permit'}
const TOTAL=Object.keys(DOCUMENTS).length
export const VEHICLE_DOCUMENT_KINDS=Object.keys(LABELS)
export const vehicleDocumentLabel=(kind:string)=>LABELS[kind]||kind.replaceAll('_',' ')

/** missing = not yet accepted; awaiting = uploaded and waiting for an administrator, so not "next to upload". */
export function documentProgress(missing:string[]|undefined,awaiting:string[]=[]):string{
  if(!missing)return ''
  if(!missing.length)return `All ${TOTAL} documents accepted`
  const waiting=missing.filter(kind=>awaiting.includes(kind)),next=missing.find(kind=>!awaiting.includes(kind))
  return [`${TOTAL-missing.length} of ${TOTAL} documents accepted`,waiting.length?`${waiting.length} waiting for review`:'',next?`Next: upload ${DOCUMENTS[next]||next}`:''].filter(Boolean).join(' · ')
}

const STATUSES:Record<string,string>={pending:'Waiting for review',approved:'Approved',rejected:'Rejected',suspended:'Suspended'}
export const truckStatus=(status:string)=>STATUSES[status]||status.replaceAll('_',' ')
