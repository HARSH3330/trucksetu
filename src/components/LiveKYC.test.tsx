import {describe,expect,it} from 'vitest'
import {verificationTypes} from './LiveKYC'

describe('provider verification type',()=>{
  it('starts on a type the account can actually submit',()=>{
    for(const roles of [['provider'],['fleet_owner'],['driver'],['provider','fleet_owner']]){
      const {options,initial}=verificationTypes(roles)
      expect(options.map(([value])=>value)).toContain(initial)
    }
  })
  it('offers each role only the types the server accepts',()=>{
    expect(verificationTypes(['provider'])).toEqual({initial:'owner',options:[['owner','Vehicle owner'],['company','Company']]})
    expect(verificationTypes(['fleet_owner']).initial).toBe('fleet')
    expect(verificationTypes(['driver'])).toEqual({initial:'driver',options:[['driver','Driver']]})
  })
})
