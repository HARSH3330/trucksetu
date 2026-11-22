import {describe,expect,it} from 'vitest'
import {bidDateProblems,bidDefaults,dateOnly,localInput,truckPaperProblem} from './bid-defaults'
import {dateTime} from './demand-types'

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

describe('bid dates must fit the customer window',()=>{
  const window={earliest_pickup_at:'2026-11-10T03:30:00Z',latest_pickup_at:'2026-11-10T09:30:00Z',delivery_deadline_at:'2026-11-11T13:30:00Z'}
  const at=(iso:string)=>localInput(iso)
  it('is quiet when pickup and delivery fit',()=>{
    expect(bidDateProblems(window,at('2026-11-10T05:00:00Z'),at('2026-11-11T13:30:00Z'))).toEqual({pickup:null,delivery:null})
    expect(bidDateProblems(window,'','')).toEqual({pickup:null,delivery:null})
  })
  it('names the pickup window when pickup is outside it',()=>{
    const message=`Pickup must be between ${dateTime(window.earliest_pickup_at)} and ${dateTime(window.latest_pickup_at)}, as the customer asked.`
    expect(bidDateProblems(window,at('2026-11-10T03:00:00Z'),at('2026-11-11T10:00:00Z')).pickup).toBe(message)
    expect(bidDateProblems(window,at('2026-11-10T10:00:00Z'),at('2026-11-11T10:00:00Z')).pickup).toBe(message)
  })
  it('names the deadline when delivery is late, and asks for delivery after pickup',()=>{
    expect(bidDateProblems(window,at('2026-11-10T05:00:00Z'),at('2026-11-11T14:00:00Z')).delivery).toBe(`Delivery must be by ${dateTime(window.delivery_deadline_at)}, the customer's deadline.`)
    expect(bidDateProblems(window,at('2026-11-10T05:00:00Z'),at('2026-11-10T05:00:00Z')).delivery).toBe('Delivery must be after pickup.')
  })
})

describe('truck papers must last until delivery',()=>{
  const truck={registration_number:'13221',document_expiries:{rc:'2030-11-14',insurance:'2030-11-14',fitness:'2026-11-16',pollution:'2030-11-14',permit:'2030-11-14'}}
  it('names the paper that expires before delivery',()=>{
    expect(truckPaperProblem(truck,localInput('2026-11-23T03:30:00Z'))).toBe(`Truck 13221's fitness certificate expires on ${dateOnly('2026-11-16')}. Choose a delivery on or before that date, or upload the renewed certificate under Fleet → Private documents.`)
  })
  it('is quiet when papers last until delivery or nothing is chosen',()=>{
    expect(truckPaperProblem(truck,localInput('2026-11-16T05:00:00Z'))).toBeNull()
    expect(truckPaperProblem(undefined,localInput('2026-11-23T03:30:00Z'))).toBeNull()
    expect(truckPaperProblem(truck,'')).toBeNull()
  })
})
