import React from 'react'
import {renderToStaticMarkup} from 'react-dom/server'
import {expect,it} from 'vitest'
import SignupConsent from './SignupConsent'

it('requires agreement and links the Terms and Privacy notice in a new tab',()=>{
  const html=renderToStaticMarkup(<SignupConsent checked={false} onChange={()=>{}} />)
  expect(html).toMatch(/<input(?=[^>]*type="checkbox")(?=[^>]*required="")[^>]*>/)
  expect(html).toMatch(/<a(?=[^>]*href="#terms")(?=[^>]*target="_blank")(?=[^>]*rel="noopener")[^>]*>Terms &amp; Conditions<\/a>/)
  expect(html).toMatch(/<a(?=[^>]*href="#privacy")(?=[^>]*target="_blank")[^>]*>Privacy notice<\/a>/)
})
