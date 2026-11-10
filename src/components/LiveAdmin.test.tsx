import {renderToStaticMarkup} from 'react-dom/server'
import {describe,expect,it} from 'vitest'
import {AdminOverview} from './LiveAdmin'

const health={verified_providers:2,approved_vehicles:3,open_requests:8,active_quotes:1,active_bookings:0,open_disputes:0,pending_kyc:0,gmv:'0',total_bookings:0,completed_bookings:0,completion_rate:0}
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
})
