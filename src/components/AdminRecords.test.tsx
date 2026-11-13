import React from 'react'
import {renderToStaticMarkup} from 'react-dom/server'
import {expect,it} from 'vitest'
import AdminRecords,{RequirementRow,UserRow} from './AdminRecords'

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
