import React from 'react'
import {renderToStaticMarkup} from 'react-dom/server'
import {expect, it} from 'vitest'
import {PublicPolicy} from './PublicInformation'

it('publishes a real privacy notice naming the company, PAN and the grievance contact', () => {
  const html = renderToStaticMarkup(<PublicPolicy kind="privacy" />)
  expect(html).toContain('TransivoX Private Limited')
  expect(html).toContain('harshagarwal244@gmail.com')
  expect(html).toContain('PAN')
  expect(html).toContain('How long we keep data')
  expect(html).not.toContain('has not yet been published')
})
it('does not ask customers for Aadhaar', () => {
  expect(renderToStaticMarkup(<PublicPolicy kind="privacy" />)).not.toMatch(/Aadhaar/i)
})
it('keeps the refund page free of hard-coded checkout claims until the server answers', () => {
  const html = renderToStaticMarkup(<PublicPolicy kind="refund" />)
  expect(html).toContain('Platform connection-fee rules')
  expect(html).toContain('Tax is pending server configuration')
})
