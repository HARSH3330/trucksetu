import {expect,it} from 'vitest'
import {kycStatusLabel,missingDocuments,providerTypeLabel,requiredDocuments} from './kyc-requirements'

it('lists the documents each verification type must upload, matching the server',()=>{
  expect(requiredDocuments('fleet')).toEqual(['PAN','Vehicle RC','GST certificate'])
  expect(requiredDocuments('owner')).toEqual(['Aadhaar','PAN','Vehicle RC'])
  expect(requiredDocuments('driver')).toEqual(['Aadhaar','PAN','Driving licence'])
})
it('names what is still missing, ignoring rejected uploads',()=>{
  expect(missingDocuments('fleet',[{type:'pan',status:'uploaded'},{type:'gst_certificate',status:'rejected'}])).toEqual(['Vehicle RC','GST certificate'])
  expect(missingDocuments('fleet',[{type:'pan',status:'uploaded'},{type:'vehicle_rc',status:'uploaded'},{type:'gst_certificate',status:'uploaded'}])).toEqual([])
})
it('shows plain words instead of internal values',()=>{
  expect(providerTypeLabel('fleet')).toBe('Fleet owner')
  expect(providerTypeLabel('owner')).toBe('Vehicle owner')
  expect(kycStatusLabel('registered')).toBe('Not yet submitted')
  expect(kycStatusLabel('under_review')).toBe('Under review')
  expect(kycStatusLabel('resubmit_required')).toBe('Changes requested')
})
