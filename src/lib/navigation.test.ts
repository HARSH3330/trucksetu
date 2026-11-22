import {describe, expect, it} from 'vitest'
import {defaultDestination,menuFor,mobileMenuFor} from './navigation'

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

const labels=(roles:string[]|null)=>menuFor(roles).map(([,label])=>label)

describe('menus match the person using the site',()=>{
  it('shows visitors and customers only customer pages, without a duplicate Bids link',()=>{
    expect(labels(null)).toEqual(['Home','Post requirement','My requirements','Price estimate','Help'])
    expect(labels(['customer'])).toEqual(['Home','Post requirement','My requirements','Bookings & trips','Price estimate','Help'])
  })
  it('shows fleet owners their own pages in plain words',()=>{
    expect(labels(['fleet_owner'])).toEqual(['Find loads','My bids','Fleet & drivers','Bookings & trips','Verification','Help'])
    expect(labels(['provider'])).toEqual(labels(['fleet_owner']))
  })
  it('keeps drivers and admins away from customer links',()=>{
    expect(labels(['driver'])).toEqual(['My trips','Help'])
    expect(labels(['admin'])).toEqual(['Control centre','Vehicle approvals','Verification','Help'])
    expect(labels(['superadmin','customer'])).toEqual(labels(['admin']))
  })
  it('gives each role a short phone menu',()=>{
    expect(mobileMenuFor(['customer']).map(([view])=>view)).toEqual(['home','ship','requirements','bookings'])
    expect(mobileMenuFor(['driver']).map(([view])=>view)).toEqual(['trips','support'])
    expect(mobileMenuFor(['admin']).map(([view])=>view)).toEqual(['admin','vehicle-review','kyc'])
  })
})
