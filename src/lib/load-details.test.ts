import {describe,expect,it} from 'vitest'
import {dateTime,loadDetails,money} from './demand-types'

const base={earliest_pickup_at:'2026-11-20T03:30:00Z',latest_pickup_at:'2026-11-20T07:30:00Z',delivery_deadline_at:'2026-11-23T03:30:00Z',budget_amount:null,cargo:{fragile:false}}

describe('schedule and terms on a load card',()=>{
  it('labels the pickup window and the delivery deadline',()=>{
    expect(loadDetails(base)).toEqual([`Pickup between ${dateTime(base.earliest_pickup_at)} and ${dateTime(base.latest_pickup_at)}`,`Deliver by ${dateTime(base.delivery_deadline_at)}`])
  })
  it('adds the customer budget and fragile goods when given',()=>{
    const lines=loadDetails({...base,budget_amount:'25000.00',cargo:{fragile:true}})
    expect(lines).toContain(`Customer budget: ${money('25000.00')}`)
    expect(lines).toContain('Fragile goods: handle with care')
  })
  it('skips times the customer did not set',()=>{
    expect(loadDetails({...base,latest_pickup_at:null,delivery_deadline_at:null})).toEqual([`Pickup from ${dateTime(base.earliest_pickup_at)}`])
  })
})
