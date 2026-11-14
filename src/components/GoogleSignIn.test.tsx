import React from 'react'
import {renderToStaticMarkup} from 'react-dom/server'
import {expect,it} from 'vitest'
import {GoogleRoleStep} from './GoogleSignIn'

const step=(agreed:boolean)=>renderToStaticMarkup(<GoogleRoleStep email="fictional@example.com" role="customer" mobile="" agreed={agreed} busy={false} onRole={()=>{}} onMobile={()=>{}} onAgree={()=>{}} onCreate={()=>{}} onCancel={()=>{}}/>)

it('asks a new Google user to choose a role and agree before creating the account',()=>{
  const html=step(false)
  expect(html).toContain('fictional@example.com')
  expect(html).toContain('Truck owner — I bid on loads')
  expect(html).not.toContain('value="admin"')
  expect(html).toMatch(/<button[^>]*disabled=""[^>]*>Create account<\/button>/)
})
it('enables account creation once the person agrees',()=>{
  expect(step(true)).toMatch(/<button class="auth-submit">Create account<\/button>/)
})
