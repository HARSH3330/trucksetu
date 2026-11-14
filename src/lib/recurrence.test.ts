import {describe, expect, it} from 'vitest'
import {createDrafts, planRecurringDrafts, validateRule, type DraftPayload} from './recurrence'

const now = new Date(2026, 10, 3, 9, 0) // 3 Nov 2026 09:00 local
const base: DraftPayload = {pickup_city: 'Pune', destination_city: 'Mumbai', start: '2026-11-10T08:00', end: '2026-11-10T12:00', deadline: '2026-11-11T18:00', description: 'Boxes', flexible: false}
const plan = (rule: {frequency: 'daily' | 'weekly' | 'monthly'; every: number; occurrences: number}, input = base, existing = 0) => planRecurringDrafts(input, rule, existing, now)

describe('recurring requirement drafts', () => {
  it('creates weekly copies that keep the pickup window and delivery deadline spacing', () => {
    const result = plan({frequency: 'weekly', every: 1, occurrences: 3})
    expect(result.error).toBeNull()
    expect(result.payloads.map(p => [p.start, p.end, p.deadline])).toEqual([
      ['2026-11-17T08:00', '2026-11-17T12:00', '2026-11-18T18:00'],
      ['2026-11-24T08:00', '2026-11-24T12:00', '2026-11-25T18:00'],
      ['2026-12-01T08:00', '2026-12-01T12:00', '2026-12-02T18:00'],
    ])
  })
  it('supports daily intervals and every-N repeats', () => {
    expect(plan({frequency: 'daily', every: 2, occurrences: 2}).payloads.map(p => p.start)).toEqual(['2026-11-12T08:00', '2026-11-14T08:00'])
  })
  it('clamps month-end dates without drifting later months and crosses year ends', () => {
    const jan31 = {...base, start: '2026-12-31T08:00', end: '', deadline: ''}
    const result = planRecurringDrafts(jan31, {frequency: 'monthly', every: 1, occurrences: 3}, 0, now)
    expect(result.payloads.map(p => p.start)).toEqual(['2027-01-31T08:00', '2027-02-28T08:00', '2027-03-31T08:00'])
  })
  it('copies every other field unchanged and never marks a copy as published or reviewed', () => {
    const [first] = plan({frequency: 'weekly', every: 1, occurrences: 1}).payloads
    expect(first).toMatchObject({pickup_city: 'Pune', destination_city: 'Mumbai', description: 'Boxes', flexible: false})
    expect(Object.keys(first).sort()).toEqual(Object.keys(base).sort())
  })
  it('does not mutate the original requirement', () => {
    const copy = JSON.stringify(base); plan({frequency: 'daily', every: 1, occurrences: 5}); expect(JSON.stringify(base)).toBe(copy)
  })
  it('refuses a past original, a missing or impossible start, and impossible dates', () => {
    expect(plan({frequency: 'daily', every: 1, occurrences: 1}, {...base, start: '2026-11-01T08:00'}).error).toMatch(/has passed/)
    expect(plan({frequency: 'daily', every: 1, occurrences: 1}, {...base, start: ''}).error).toMatch(/no valid pickup start/)
    expect(plan({frequency: 'daily', every: 1, occurrences: 1}, {...base, start: '2027-02-31T08:00'}).error).toMatch(/no valid pickup start/)
    expect(plan({frequency: 'daily', every: 1, occurrences: 1}, {...base, end: 'tomorrow'}).error).toMatch(/invalid pickup or delivery/)
  })
  it('enforces interval, copy count and the 30-draft limit', () => {
    expect(validateRule({frequency: 'daily', every: 0, occurrences: 1}, 0)).toMatch(/interval/)
    expect(validateRule({frequency: 'daily', every: 1, occurrences: 13}, 0)).toMatch(/between 1 and 12/)
    expect(validateRule({frequency: 'daily', every: 1.5, occurrences: 1}, 0)).toMatch(/interval/)
    expect(validateRule({frequency: 'daily', every: 1, occurrences: 5}, 26)).toMatch(/at most 30/)
    expect(validateRule({frequency: 'daily', every: 1, occurrences: 4}, 26)).toBeNull()
  })
})

describe('creating the drafts', () => {
  it('stops at the first failure and reports exactly how many were created', async () => {
    let calls = 0
    const result = await createDrafts(async () => { calls += 1; if (calls === 3) throw new Error('Server unavailable') }, [base, base, base, base])
    expect(result).toEqual({created: 2, error: 'Server unavailable'})
    expect(calls).toBe(3)
  })
  it('reports full success', async () => {
    expect(await createDrafts(async () => undefined, [base, base])).toEqual({created: 2, error: null})
  })
})
