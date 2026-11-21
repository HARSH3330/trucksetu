import React from 'react'
import {renderToStaticMarkup} from 'react-dom/server'
import {expect,it} from 'vitest'
import AdminRecords,{AuditRow,BookingRow,DisputeRow,RequirementRow,UserRow} from './AdminRecords'

const person={id:'u1',name:'Fictional Fleet',email:'fleet@example.com',status:'active',roles:['fleet_owner'],email_verified:false,mobile:'••••0001',mobile_verified:true,customer_kyc_status:null,provider_kyc_status:'registered'}
const noop=()=>{}

it('shows loading without invented admin records',()=>{
  const html=renderToStaticMarkup(<AdminRecords/>);
  expect(html).toContain('Loading operational records')
  expect(html).not.toContain('Harsh')
  expect(html).toContain('>Requirements</button>')
})

it('opens the status form right under the person, not at the bottom of the page',()=>{
  const closed=renderToStaticMarkup(<UserRow item={person} open={false} busy={false} onOpen={noop} onClose={noop} onSaved={noop}/>)
  expect(closed).toContain('class="admin-record"')
  expect(closed).toMatch(/<button[^>]*>Change account status<\/button>/)
  const open=renderToStaticMarkup(<UserRow item={person} open busy={false} onOpen={noop} onClose={noop} onSaved={noop}/>)
  expect(open).toMatch(/<article class="admin-record">.*Change status: Fictional Fleet.*<\/article>/s)
  expect(open).toContain('Suspend')
  expect(open).toContain('signed out everywhere')
})

it('never offers status changes for admin accounts',()=>{
  const html=renderToStaticMarkup(<UserRow item={{...person,roles:['superadmin']}} open={false} busy={false} onOpen={noop} onClose={noop} onSaved={noop}/>)
  expect(html).not.toContain('Change account status')
  expect(html).toContain('Admin accounts are managed separately')
})

it('shows each verification status in words on every account',()=>{
  const html=renderToStaticMarkup(<UserRow item={person} open={false} busy={false} onOpen={noop} onClose={noop} onSaved={noop}/>)
  expect(html).toContain('Email: not verified')
  expect(html).toContain('Phone ••••0001: verified')
  expect(html).toContain('Provider verification: registered')
  expect(html).not.toContain('Edit verification')
})

it('lets only the superadmin edit email and phone verification, with a reason',()=>{
  const closed=renderToStaticMarkup(<UserRow item={person} superadmin open={false} busy={false} onOpen={noop} onClose={noop} onSaved={noop}/>)
  expect(closed).toMatch(/<button[^>]*>Edit verification<\/button>/)
  const open=renderToStaticMarkup(<UserRow item={person} superadmin open="verification" busy={false} onOpen={noop} onClose={noop} onSaved={noop}/>)
  expect(open).toContain('Edit verification: Fictional Fleet')
  expect(open).toContain('Mark email verified')
  expect(open).toContain('Mark phone not verified')
  expect(open).toContain('kept in the audit log')
  expect(open).not.toContain('Change status:')
})

it('lists requirements with a clear TEST badge and bid count',()=>{
  const html=renderToStaticMarkup(<RequirementRow item={{id:'r1',reference:'TS-REQ-2026-T8123',route:'Mumbai → Pune',status:'published',pickup_date:'2026-11-13',customer_name:'TransivoX TEST customer',bid_count:0,is_test:true}}/>)
  expect(html).toContain('TS-REQ-2026-T8123')
  expect(html).toContain('Mumbai → Pune')
  expect(html).toContain('TEST data')
  expect(html).toContain('0 bids')
})

it('warns when the phone is already verified on another account and asks the superadmin to confirm',()=>{
  const shared={...person,email_verified:true,mobile_verified:false,mobile_shared_count:1}
  expect(renderToStaticMarkup(<UserRow item={shared} open={false} busy={false} onOpen={noop} onClose={noop} onSaved={noop}/>)).toContain('Warning: this phone number is also verified on 1 other account')
  const open=renderToStaticMarkup(<UserRow item={shared} superadmin open="verification" busy={false} onOpen={noop} onClose={noop} onSaved={noop}/>)
  expect(open).toContain('Mark phone verified')
  expect(open).toMatch(/role="alert"[^>]*>.*also verified on 1 other account/s)
  expect(open).toMatch(/<input type="checkbox" required=""[^>]*\/>Verify anyway/)
})

it('offers dispute and audit tabs next to the other records',()=>{
  const html=renderToStaticMarkup(<AdminRecords/>)
  expect(html).toContain('>Disputes</button>')
  expect(html).toContain('>Audit log</button>')
  expect(renderToStaticMarkup(<AdminRecords initialTab="disputes"/>)).toMatch(/aria-pressed="true"[^>]*>Disputes</)
})

it('shows who serves a booking, its trips, disputes and connection fee without contact details',()=>{
  const html=renderToStaticMarkup(<BookingRow item={{id:'b1',reference:'TS-BK-1',customer_name:'Fictional Customer',status:'disputed',total_amount:'750.00',provider_names:['Fictional Fleet'],trip_statuses:['driver_assigned'],driver_assigned:true,open_disputes:1,connection_fee:{status:'paid',payment_status:'captured',contact_revealed:true}}}/>)
  expect(html).toContain('TS-BK-1')
  expect(html).toContain('Fictional Fleet')
  expect(html).toContain('Trips: driver assigned · driver assigned')
  expect(html).toContain('1 open dispute')
  expect(html).toContain('Connection fee: paid · payment captured · contact revealed')
})

const dispute={id:'d1',booking_id:'b1',booking_reference:'TS-BK-1',booking_status:'disputed',category:'delivery_delay',description:'The fictional truck never arrived.',status:'open',priority:'normal',raised_by_name:'Fictional Customer',resolution:null,resolved_at:null,created_at:'2026-11-15T10:00:00Z',restores_booking_to:'booking_confirmed'}
it('lets an admin resolve an open dispute only with a written resolution',()=>{
  const closed=renderToStaticMarkup(<DisputeRow item={dispute} open={false} busy={false} onOpen={noop} onClose={noop} onSaved={noop}/>)
  expect(closed).toContain('The fictional truck never arrived.')
  expect(closed).toContain('delivery delay')
  expect(closed).toMatch(/<button[^>]*>Resolve dispute<\/button>/)
  const open=renderToStaticMarkup(<DisputeRow item={dispute} open busy={false} onOpen={noop} onClose={noop} onSaved={noop}/>)
  expect(open).toContain('Resolve dispute: TS-BK-1')
  expect(open).toContain('booking goes back to booking confirmed')
  expect(open).toContain('kept in the audit log')
  expect(open).toMatch(/<button disabled=""[^>]*>Confirm resolution<\/button>/)
  const resolved=renderToStaticMarkup(<DisputeRow item={{...dispute,status:'resolved',resolution:'Rescheduled pickup.'}} open={false} busy={false} onOpen={noop} onClose={noop} onSaved={noop}/>)
  expect(resolved).not.toContain('Resolve dispute')
  expect(resolved).toContain('Resolution: Rescheduled pickup.')
})

it('shows who did what, why and what changed in the audit log',()=>{
  const html=renderToStaticMarkup(<AuditRow item={{id:'a1',actor_id:'u9',actor_name:'Fictional Owner',actor_email:'ow•••@example.com',action:'dispute.resolved',entity_type:'dispute',entity_id:'d1',reason:'Rescheduled pickup.',changes:{status:['open','resolved']},request_id:null,created_at:'2026-11-15T10:00:00Z'}}/>)
  expect(html).toContain('dispute.resolved')
  expect(html).toContain('Fictional Owner')
  expect(html).toContain('Reason: Rescheduled pickup.')
  expect(html).toContain('status: open → resolved')
  const system=renderToStaticMarkup(<AuditRow item={{id:'a2',actor_id:null,actor_name:null,actor_email:null,action:'connection.refund_reconciled',entity_type:'demand_selection',entity_id:null,reason:null,changes:{},request_id:null,created_at:'2026-11-15T10:00:00Z'}}/>)
  expect(system).toContain('System')
})
