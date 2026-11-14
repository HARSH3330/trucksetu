import {describe, expect, it} from 'vitest'
import {tripReadPath, canOperateTrips, tripActions} from './trips'

describe('trip role boundary',()=>{
  it('reads assigned trips for drivers instead of general bookings',()=>{
    expect(tripReadPath(['driver'])).toBe('/drivers/me/trips')
    expect(tripReadPath(['provider'])).toBe('/bookings')
    expect(tripReadPath(['customer'])).toBe('/bookings')
    expect(tripReadPath(['admin','driver'])).toBe('/bookings')
  })
  it('offers operator controls to assigned-driver accounts but not customers',()=>{
    expect(canOperateTrips(['driver'])).toBe(true)
    expect(canOperateTrips(['provider'])).toBe(true)
    expect(canOperateTrips(['customer'])).toBe(false)
    expect(canOperateTrips([])).toBe(false)
  })
})

import * as tripRules from './trips'
it('blocks operations while connection payment or cancellation blocks the booking',()=>{
 const allowed=(tripRules as unknown as {canRunTripActions?:(status:string,available?:boolean)=>boolean}).canRunTripActions
 expect(allowed).toBeTypeOf('function')
 if(!allowed)return
 for(const status of ['connection_fee_pending','cancelled','disputed'])expect(allowed(status)).toBe(false)
 expect(allowed('booking_confirmed',false)).toBe(false)
 expect(allowed('booking_confirmed',true)).toBe(true)
})

it('offers a stop update only when the load has stops',()=>{
  expect(tripActions('in_transit',0)).toEqual(['arrived_at_destination','on_hold'])
  expect(tripActions('in_transit',2)).toEqual(['at_stop','arrived_at_destination','on_hold'])
  expect(tripActions('loaded',undefined)).toEqual(['in_transit'])
  expect(tripActions('completed',0)).toEqual([])
})
