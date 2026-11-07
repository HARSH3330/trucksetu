const DOCUMENTS:Record<string,string>={rc:'the registration certificate (RC)',insurance:'the insurance',fitness:'the fitness certificate',pollution:'the pollution certificate',permit:'the permit'}
const TOTAL=Object.keys(DOCUMENTS).length

export function documentProgress(missing:string[]|undefined):string{
  if(!missing)return ''
  if(!missing.length)return `All ${TOTAL} documents accepted`
  return `${TOTAL-missing.length} of ${TOTAL} documents accepted · Next: upload ${DOCUMENTS[missing[0]]||missing[0]}`
}

const STATUSES:Record<string,string>={pending:'Waiting for review',approved:'Approved',rejected:'Rejected',suspended:'Suspended'}
export const truckStatus=(status:string)=>STATUSES[status]||status.replaceAll('_',' ')
