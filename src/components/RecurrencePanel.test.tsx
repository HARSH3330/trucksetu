import React from 'react'
import {renderToStaticMarkup} from 'react-dom/server'
import {expect, it} from 'vitest'
import RecurrencePanel from './RecurrencePanel'

const future = new Date(Date.now() + 5 * 86_400_000)
const local = (d: Date) => new Date(d.getTime() - d.getTimezoneOffset() * 60000).toISOString().slice(0, 16)
const noop = () => {}

it('states plainly that repeating only creates drafts and previews the dates', () => {
  const html = renderToStaticMarkup(<RecurrencePanel base={{start: local(future), end: '', deadline: ''}} label="Pune → Mumbai" existingDrafts={0} onDone={noop} onClose={noop} />)
  expect(html).toContain('Nothing is published')
  expect(html).toContain('Create 4 draft(s)')
  expect((html.match(/<li>/g) || []).length).toBe(4)
})
it('disables creation and explains when the original pickup time is missing', () => {
  const html = renderToStaticMarkup(<RecurrencePanel base={{start: '', end: '', deadline: ''}} label="x" existingDrafts={0} onDone={noop} onClose={noop} />)
  expect(html).toContain('no valid pickup start')
  expect(html).toMatch(/<button[^>]*disabled=""[^>]*>Create\s+draft\(s\)/)
})
it('blocks creation when it would exceed the draft limit', () => {
  const html = renderToStaticMarkup(<RecurrencePanel base={{start: local(future), end: '', deadline: ''}} label="x" existingDrafts={28} onDone={noop} onClose={noop} />)
  expect(html).toContain('at most 30 drafts')
})
