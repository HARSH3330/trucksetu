import {expect,it} from 'vitest'
import {signupBody} from './signup'

const form={name:'Fictional Customer',email:'fictional@example.com',mobile:' +91 98765 43210 ',password:'Fictional123',role:'customer'}

it('sends the Terms version the person agreed to at signup',()=>{
  expect(signupBody(form,'privacy-v4',"2026-11-11-v2")).toMatchObject({terms_version:'2026-11-11-v2',privacy_notice_version:'privacy-v4',mobile:'+91 98765 43210'})
})

it('leaves the Terms out when their version could not be loaded',()=>{
  expect(signupBody({...form,mobile:''},'privacy-v4',null)).not.toHaveProperty('terms_version')
  expect(signupBody({...form,mobile:''},'privacy-v4',null).mobile).toBeNull()
})
