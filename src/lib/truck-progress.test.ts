import {expect,it} from 'vitest'
import {documentProgress,truckStatus,vehicleDocumentLabel} from './truck-progress'

it('says how many of the five truck documents are accepted and what to upload next',()=>{
  expect(documentProgress([])).toBe('All 5 documents accepted')
  expect(documentProgress(['pollution','rc'])).toBe('3 of 5 documents accepted · Next: upload the pollution certificate')
  expect(documentProgress(undefined)).toBe('')
})
it('names truck review states in plain words',()=>{
  expect(truckStatus('pending')).toBe('Waiting for review')
  expect(truckStatus('approved')).toBe('Approved')
  expect(truckStatus('something_new')).toBe('something new')
})
it('counts uploaded files as waiting for review and points to the next file still to upload',()=>{
  expect(documentProgress(['fitness','permit','pollution'],['fitness','permit','pollution'])).toBe('2 of 5 documents accepted · 3 waiting for review')
  expect(documentProgress(['fitness','permit'],['fitness'])).toBe('3 of 5 documents accepted · 1 waiting for review · Next: upload the permit')
})
it('labels truck document types for people',()=>{
  expect(vehicleDocumentLabel('rc')).toBe('Registration certificate (RC)')
  expect(vehicleDocumentLabel('pollution')).toBe('Pollution certificate (PUC)')
})
