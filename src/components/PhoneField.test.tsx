import {renderToStaticMarkup} from 'react-dom/server'
import {describe,expect,it} from 'vitest'
import {GoogleRoleStep} from './GoogleSignIn'
import {PhoneField,phoneRequired} from './SignupHelp'

describe('phone number at sign-up',()=>{
  it('is required for the roles that bid or drive, optional for customers',()=>{
    expect(['provider','fleet_owner','driver'].every(phoneRequired)).toBe(true)
    expect(phoneRequired('customer')).toBe(false)
    const work=renderToStaticMarkup(<PhoneField role="provider" value="" onChange={()=>{}}/>)
    expect(work).toMatch(/Mobile number<input[^>]*required=""/)
    expect(work).toContain('Customers see this number after they pay for your bid')
    const customer=renderToStaticMarkup(<PhoneField role="customer" value="" onChange={()=>{}}/>)
    expect(customer).toContain('Mobile (optional)')
    expect(customer).not.toContain('required=""')
  })
  it('is asked for in the Google sign-up step too',()=>{
    const html=renderToStaticMarkup(<GoogleRoleStep email="fictional@example.com" role="fleet_owner" mobile="" agreed busy={false} onRole={()=>{}} onMobile={()=>{}} onAgree={()=>{}} onCreate={()=>{}} onCancel={()=>{}}/>)
    expect(html).toMatch(/Mobile number<input[^>]*required=""/)
  })
})
