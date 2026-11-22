import React from 'react'
import {renderToStaticMarkup} from 'react-dom/server'
import {expect,it} from 'vitest'
import {AdminVerification,VerificationSignedOut,applicationTitle} from './CustomerVerification'

it('names the account holder before the application number',()=>{
  const item={id:'1a2b3c4d-0000-0000-0000-000000000000',account_name:'Fictional Customer',account_email:'fictional@example.com'}
  expect(applicationTitle(item)).toBe('Fictional Customer · Application 1a2b3c4d')
  expect(applicationTitle({id:item.id})).toBe('Application 1a2b3c4d')
})

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
