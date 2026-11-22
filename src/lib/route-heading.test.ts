import {expect,it} from 'vitest'
import {routeEnds} from './demand-types'

it('uses the exact pickup and drop address when the viewer may see them',()=>{
  expect(routeEnds({pickup_city:'New Delhi',destination_city:'Noida',pickup_address:'Gate 3, Okhla Phase 2, New Delhi 110020',destination_address:'Plot 14, Sector 63, Noida 201301'}))
    .toEqual({from:'Gate 3, Okhla Phase 2, New Delhi 110020',to:'Plot 14, Sector 63, Noida 201301',exact:true})
})

it('falls back to the cities for truck owners still under review',()=>{
  expect(routeEnds({pickup_city:'New Delhi',destination_city:'Noida'})).toEqual({from:'New Delhi',to:'Noida',exact:false})
  expect(routeEnds({pickup_city:'New Delhi',destination_city:'Noida',pickup_address:'  ',destination_address:null})).toEqual({from:'New Delhi',to:'Noida',exact:false})
})
