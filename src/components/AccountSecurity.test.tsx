import React from 'react'
import {renderToStaticMarkup} from 'react-dom/server'
import {expect,it} from 'vitest'
import AccountSecurity,{emailVerifiedMessage} from './AccountSecurity'

it('does not ask a signed-in person to sign in again after verifying email',()=>{
  expect(emailVerifiedMessage(true)).toBe('Email verified. Your account is updated; you can close this window.')
  expect(emailVerifiedMessage(true)).not.toMatch(/sign in again/i)
  expect(emailVerifiedMessage(false)).toBe('Email verified. Sign in to continue.')
})

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
it('is a focusable modal dialog so keyboard users can reach and close it',()=>{
  expect(renderToStaticMarkup(<AccountSecurity close={()=>{}}/>)).toMatch(/<div(?=[^>]*role="dialog")(?=[^>]*tabindex="-1")[^>]*>/)
})
