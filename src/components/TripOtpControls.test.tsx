import React from 'react'
import {renderToStaticMarkup} from 'react-dom/server'
import {expect,it} from 'vitest'
import TripOtpControls from './TripOtpControls'

const render=(roles:string[],status='arrived_at_pickup')=>renderToStaticMarkup(<TripOtpControls roles={roles} status={status} busy={false} onIssue={async()=>{}} onVerify={async()=>true}/>)
it('lets customers request pickup delivery but not enter operator verification',()=>{
  const html=render(['customer'])
  expect(html).toContain('Request pickup OTP')
  expect(html).not.toContain('Verify pickup OTP')
})
it('lets drivers verify delivery but not issue customer codes',()=>{
  const html=render(['driver'],'arrived_at_destination')
  expect(html).toContain('Verify delivery OTP')
  expect(html.toLowerCase()).toContain('inputmode="numeric"')
  expect(html).not.toContain('Request delivery OTP')
})
it('offers no OTP actions outside legal arrival states',()=>{
  expect(render(['admin'],'in_transit')).toBe('')
  expect(render([])).not.toContain('<button')
})
