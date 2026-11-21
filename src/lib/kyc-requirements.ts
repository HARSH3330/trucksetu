/** Mirrors REQUIRED in backend/app/api/kyc.py so the page can say what to upload before submission. */
export const KYC_DOCUMENT_LABELS:Record<string,string>={aadhaar:'Aadhaar',pan:'PAN',driving_licence:'Driving licence',vehicle_rc:'Vehicle RC',gst_certificate:'GST certificate',bank_proof:'Bank proof',vehicle_insurance:'Vehicle insurance',fitness_certificate:'Fitness certificate',commercial_permit:'Commercial permit',pollution_certificate:'Pollution certificate'}
const REQUIRED:Record<string,string[]>={driver:['aadhaar','pan','driving_licence'],owner:['aadhaar','pan','vehicle_rc'],fleet:['pan','vehicle_rc','gst_certificate'],company:['pan','vehicle_rc','gst_certificate']}
const required=(type:string|null|undefined)=>REQUIRED[type||'']||REQUIRED.driver

export const requiredDocuments=(type:string|null|undefined)=>required(type).map(key=>KYC_DOCUMENT_LABELS[key])
export const requiredDocumentKeys=(type:string|null|undefined)=>[...required(type)]
export function missingDocuments(type:string|null|undefined,documents:{type:string;status:string}[]):string[]{
  const present=new Set(documents.filter(item=>item.status!=='rejected').map(item=>item.type))
  return required(type).filter(key=>!present.has(key)).map(key=>KYC_DOCUMENT_LABELS[key])
}
const TYPES:Record<string,string>={driver:'Driver',owner:'Vehicle owner',fleet:'Fleet owner',company:'Company'}
export const providerTypeLabel=(type:string|null|undefined)=>TYPES[type||'']||'Provider'
const STATUSES:Record<string,string>={registered:'Not yet submitted',under_review:'Under review',verified:'Verified',resubmit_required:'Changes requested',rejected:'Rejected',suspended:'Suspended',uploaded:'Uploaded',accepted:'Accepted'}
export const kycStatusLabel=(status:string)=>STATUSES[status]||status.replaceAll('_',' ')
