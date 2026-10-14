import {describe, expect, it} from 'vitest'
import {defaultDestination} from './navigation'

describe('API user role navigation',()=>{
  it.each([
    ['admin','admin'], ['superadmin','admin'], ['provider','dashboard'],
    ['fleet_owner','dashboard'], ['driver','trips'], ['customer','dashboard'],
  ])('routes %s to %s',(role,destination)=>{
    expect(defaultDestination({id:'fictional',full_name:'Fictional user',roles:[role]})).toBe(destination)
  })
  it('prioritizes privileged roles over public roles regardless of order',()=>{
    for(const roles of [['customer','admin'],['superadmin','provider'],['driver','fleet_owner']]){
      expect(defaultDestination({id:'fictional',full_name:'Fictional user',roles})).toBe(roles.includes('fleet_owner')?'dashboard':'admin')
    }
  })
  it('does not route unknown or signed-out roles to a protected destination',()=>{
    expect(defaultDestination(null)).toBe('home')
    expect(defaultDestination({id:'fictional',full_name:'Fictional user',roles:['unrecognized']})).toBe('home')
    expect(defaultDestination({id:'fictional',full_name:'Fictional user',roles:[]})).toBe('home')
  })
})
