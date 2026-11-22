import {describe,expect,it} from 'vitest'
import {roadDistance} from './demand-types'

describe('road distance on a load card',()=>{
  it('shows km by road and the driving time',()=>{
    expect(roadDistance({route_distance_km:'412.35',route_duration_minutes:455})).toBe('412 km by road · about 7 h 35 min drive')
    expect(roadDistance({route_distance_km:'8.4',route_duration_minutes:25})).toBe('8.4 km by road · about 25 min drive')
    expect(roadDistance({route_distance_km:'120',route_duration_minutes:null})).toBe('120 km by road')
  })
  it('says honestly when the distance is not known yet',()=>{
    expect(roadDistance({route_distance_km:null,route_duration_minutes:null})).toBe('Road distance not available yet')
    expect(roadDistance({})).toBe('Road distance not available yet')
  })
})
