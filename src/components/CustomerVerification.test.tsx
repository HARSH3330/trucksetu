import React from 'react'
import {renderToStaticMarkup} from 'react-dom/server'
import {expect,it} from 'vitest'
import {VerificationSignedOut} from './CustomerVerification'

it('asks signed-out visitors to sign in instead of reporting a session change',()=>{
  const html=renderToStaticMarkup(<VerificationSignedOut onSignIn={()=>{}}/>)
  expect(html).toContain('Sign in to verify your account')
  expect(html).toMatch(/<button[^>]*>Sign in<\/button>/)
  expect(html).not.toContain('Session changed')
})
