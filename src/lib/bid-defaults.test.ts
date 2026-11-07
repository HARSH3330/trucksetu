import {describe,expect,it} from 'vitest'
import {bidDefaults,localInput} from './bid-defaults'

const demand={earliest_pickup_at:'2026-11-10T03:30:00Z',delivery_deadline_at:'2026-11-10T13:30:00Z'}
const truck=(id:string,ok=true)=>({id,status:ok?'approved':'pending',document_eligible_today:ok})
const now=new Date('2026-11-08T03:30:00Z')

describe('bid form starts filled in',()=>{
  it("uses the customer's earliest pickup and delivery deadline",()=>{
    const values=bidDefaults(demand,[truck('a')],now)
    expect(values.pickup).toBe(localInput(demand.earliest_pickup_at))
    expect(values.delivery).toBe(localInput(demand.delivery_deadline_at))
  })
  it('keeps the bid open for 24 hours, but never past pickup',()=>{
    expect(bidDefaults(demand,[],now).expiry).toBe(localInput(new Date(now.getTime()+24*3600000).toISOString()))
    const soon={...demand,earliest_pickup_at:'2026-11-08T09:30:00Z'}
    expect(bidDefaults(soon,[],now).expiry).toBe(localInput(soon.earliest_pickup_at))
    expect(bidDefaults({...demand,earliest_pickup_at:'2026-11-08T03:00:00Z'},[],now).expiry).toBe('')
  })
  it('chooses the truck only when exactly one is eligible',()=>{
    expect(bidDefaults(demand,[truck('a'),truck('b',false)],now).vehicle).toBe('a')
    expect(bidDefaults(demand,[truck('a'),truck('b')],now).vehicle).toBe('')
  })
})
