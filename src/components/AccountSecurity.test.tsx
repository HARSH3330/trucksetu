import React from 'react'
import {renderToStaticMarkup} from 'react-dom/server'
import {expect,it} from 'vitest'
import AccountSecurity from './AccountSecurity'

it('does not show password or token fields before requesting recovery',()=>{
  const html=renderToStaticMarkup(<AccountSecurity close={()=>{}}/>)
  expect(html).toContain('Request recovery email')
  expect(html).not.toContain('name="token"')
})
it('masks reset tokens and requires the new password in reset mode',()=>{
  const html=renderToStaticMarkup(<AccountSecurity close={()=>{}} initialMode="reset"/>)
  expect(html).toMatch(/<input(?=[^>]*type="password")(?=[^>]*name="token")[^>]*>/)
  expect(html).toContain('New password')
})
it('provides both resend and email-code verification controls',()=>{
  const html=renderToStaticMarkup(<AccountSecurity close={()=>{}} initialMode="verify"/>)
  expect(html).toContain('Request verification email')
  expect(html).toContain('Verify email code')
})

it('requires current-password confirmation to change trip contact when signed in',()=>{
  const html=renderToStaticMarkup(<AccountSecurity close={()=>{}} signedIn initialMode="mobile"/>)
  expect(html).toContain('Mobile for trip OTP')
  expect(html).toContain('Current password')
  expect(html).toContain('Save trip contact')
})
