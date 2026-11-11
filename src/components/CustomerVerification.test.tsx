import React from 'react'
import {renderToStaticMarkup} from 'react-dom/server'
import {expect,it} from 'vitest'
import {AdminVerification,VerificationSignedOut} from './CustomerVerification'

it('puts both admin review queues on one page without stacking full-height pages',()=>{
  const html=renderToStaticMarkup(<AdminVerification/>)
  expect(html.match(/<main/g)).toHaveLength(1)
  expect(html.match(/class="page[ "]/g)).toHaveLength(1)
  expect(html.indexOf('Customer document review')).toBeLessThan(html.indexOf('provider-review'))
})

it('asks signed-out visitors to sign in instead of reporting a session change',()=>{
  const html=renderToStaticMarkup(<VerificationSignedOut onSignIn={()=>{}}/>)
  expect(html).toContain('Sign in to verify your account')
  expect(html).toMatch(/<button[^>]*>Sign in<\/button>/)
  expect(html).not.toContain('Session changed')
})
