import {renderToStaticMarkup} from 'react-dom/server'
import {describe,expect,it} from 'vitest'
import {AdminOverview} from './LiveAdmin'

const health={verified_providers:2,approved_vehicles:3,open_requests:8,active_quotes:1,active_bookings:0,open_disputes:0,pending_kyc:0,gmv:'0',total_bookings:0,completed_bookings:0,completion_rate:0,
  open_requirements:5,open_bids:7,requirements_without_bids:2,total_customers:11,total_truck_owners:4,verified_truck_owners:1,total_trucks:6,total_drivers:3,total_trips:9,active_trips:1,completed_trips:8,paid_connections:2,pending_customer_kyc:0,unverified_contacts:0}
const noop=()=>{}
const view=(overrides={})=>renderToStaticMarkup(<AdminOverview health={{...health,...overrides}} openKyc={noop} openVehicles={noop} openDisputes={noop}/>)

describe('control centre overview',()=>{
  it('puts what needs attention first, then the key numbers',()=>{
    const html=view({pending_kyc:2,open_disputes:1})
    expect(html.indexOf('Needs your attention')).toBeLessThan(html.indexOf('Open requirements'))
    expect(html).toMatch(/2 verifications waiting.*Review verifications/s)
    expect(html).toMatch(/1 open dispute.*Open disputes/s)
    expect(html).toContain('Truck approvals')
  })
  it('says plainly when nothing is waiting',()=>{
    expect(view()).toContain('No verifications or disputes are waiting')
  })
  it('shows every key number in one place',()=>{
    const html=view()
    for(const label of ['Verified truck owners','Approved trucks','Open requirements','Active bids','Active bookings','Booking value'])expect(html).toContain(label)
  })
  it('shows the whole marketplace at a glance for the owner',()=>{
    const html=view()
    for(const [label,value] of [['Open requirements','5'],['Open bids','7'],['Customers','11'],['Truck owners','4'],['Trucks','6'],['Drivers','3'],['Trips','9'],['Paid connections','2']])expect(html).toMatch(new RegExp(`${label}</small><strong>${value}</strong>`))
    expect(html).toContain('2 without bids')
    expect(html).toContain('Verified truck owners: 1')
    expect(html).toContain('1 in progress · 8 completed')
  })
  it('counts customer PAN reviews and unverified contacts as waiting work',()=>{
    const html=view({pending_customer_kyc:2,unverified_contacts:4})
    expect(html).toMatch(/2 verifications waiting/)
    expect(html).toMatch(/4 accounts without a verified email or phone/)
  })
})
