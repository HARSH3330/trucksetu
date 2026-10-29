import {describe,expect,it} from 'vitest'
import {parseAccountEmailLink} from './account-email-link'

describe('account email links',()=>{
  it('parses a reset token without submitting it',()=>{
    expect(parseAccountEmailLink('#account-reset?email=fictional%40example.com&token='+'a'.repeat(43))).toEqual({mode:'reset',email:'fictional@example.com',token:'a'.repeat(43),code:''})
  })
  it('accepts only complete known link formats',()=>{
    expect(parseAccountEmailLink('#account-verify?email=fictional%40example.com&code=123456')?.mode).toBe('verify')
    for(const hash of ['#home','#account-reset?email=a%40b.com&token=short','#account-verify?email=a%40b.com&code=oops'])expect(parseAccountEmailLink(hash)).toBeNull()
  })
})
