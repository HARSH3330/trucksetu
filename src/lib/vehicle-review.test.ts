import {expect,it} from 'vitest'
import {approvalBlocker} from './vehicle-review'

const ready={missing_accepted_documents:[] as string[],awaiting_review_documents:[] as string[],document_expiries:{rc:'2099-01-01'}}

it('allows approval once every document is accepted and current',()=>{
  expect(approvalBlocker(ready,new Date('2026-11-14'))).toBeNull()
})
it('names the documents that still need accepting before a truck can be approved',()=>{
  expect(approvalBlocker({...ready,missing_accepted_documents:['fitness','rc'],awaiting_review_documents:['fitness','rc']},new Date('2026-11-14')))
    .toBe('Accept these documents under Private document review first: Fitness certificate, Registration certificate.')
})
it('says which documents were never uploaded',()=>{
  expect(approvalBlocker({...ready,missing_accepted_documents:['permit','rc'],awaiting_review_documents:['rc']},new Date('2026-11-14')))
    .toBe('Accept these documents under Private document review first: Registration certificate. Not uploaded yet: Commercial permit.')
})
it('asks for renewal when a document has expired',()=>{
  expect(approvalBlocker({...ready,document_expiries:{rc:'2026-11-01'}},new Date('2026-11-14'))).toBe('Renew expired documents before approval.')
})
