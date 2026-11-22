export type Frequency = 'daily' | 'weekly' | 'monthly'
export type RecurrenceRule = {frequency: Frequency; every: number; occurrences: number}
export type DraftPayload = Record<string, string | boolean>

export const MAX_OCCURRENCES = 12
export const MAX_EVERY = 12
/** The drafts list shows 30 items, so refuse to create drafts that would be hidden. */
export const DRAFT_LIMIT = 30

const PATTERN = /^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2})$/

/** Wall-clock arithmetic on "YYYY-MM-DDTHH:mm" values; no time-zone or DST conversion is applied. */
function parse(value: string): number | null {
  const match = PATTERN.exec(value)
  if (!match) return null
  const [, y, mo, d, h, mi] = match.map(Number)
  const ms = Date.UTC(y, mo - 1, d, h, mi)
  const back = new Date(ms)
  // Reject impossible dates such as 2026-02-31 instead of letting them roll over.
  return back.getUTCFullYear() === y && back.getUTCMonth() === mo - 1 && back.getUTCDate() === d ? ms : null
}

function format(ms: number): string {
  return new Date(ms).toISOString().slice(0, 16)
}

function shiftMonths(ms: number, months: number): number {
  const date = new Date(ms)
  const target = date.getUTCMonth() + months
  const year = date.getUTCFullYear() + Math.floor(target / 12)
  const month = ((target % 12) + 12) % 12
  const lastDay = new Date(Date.UTC(year, month + 1, 0)).getUTCDate()
  return Date.UTC(year, month, Math.min(date.getUTCDate(), lastDay), date.getUTCHours(), date.getUTCMinutes())
}

export function occurrenceStart(startMs: number, rule: RecurrenceRule, index: number): number {
  const steps = rule.every * index
  if (rule.frequency === 'monthly') return shiftMonths(startMs, steps)
  return startMs + steps * (rule.frequency === 'weekly' ? 7 : 1) * 86_400_000
}

export function validateRule(rule: RecurrenceRule, existingDrafts: number): string | null {
  if (!Number.isInteger(rule.every) || rule.every < 1 || rule.every > MAX_EVERY) return `Repeat interval must be between 1 and ${MAX_EVERY}.`
  if (!Number.isInteger(rule.occurrences) || rule.occurrences < 1 || rule.occurrences > MAX_OCCURRENCES) return `Create between 1 and ${MAX_OCCURRENCES} copies at a time.`
  if (existingDrafts + rule.occurrences > DRAFT_LIMIT) return `You can keep at most ${DRAFT_LIMIT} drafts. Publish or discard some first.`
  return null
}

export type Plan = {payloads: DraftPayload[]; error: null} | {payloads: []; error: string}

/**
 * Builds draft payloads for the next occurrences of an existing requirement.
 * Pickup start/end and the delivery deadline keep their original spacing. Nothing is
 * published: every payload is only a draft the customer must review.
 */
export function planRecurringDrafts(base: DraftPayload, rule: RecurrenceRule, existingDrafts: number, now: Date = new Date()): Plan {
  const invalid = validateRule(rule, existingDrafts)
  if (invalid) return {payloads: [], error: invalid}
  const start = typeof base.start === 'string' ? parse(base.start) : null
  if (start === null) return {payloads: [], error: 'This requirement has no valid pickup start time to repeat.'}
  const end = typeof base.end === 'string' && base.end ? parse(base.end) : null
  const deadline = typeof base.deadline === 'string' && base.deadline ? parse(base.deadline) : null
  if ((base.end && end === null) || (base.deadline && deadline === null)) return {payloads: [], error: 'This requirement has an invalid pickup or delivery time.'}
  const nowWall = Date.UTC(now.getFullYear(), now.getMonth(), now.getDate(), now.getHours(), now.getMinutes())
  if (start <= nowWall) return {payloads: [], error: 'The original pickup time has passed. Edit it first, then repeat.'}
  const payloads: DraftPayload[] = []
  for (let index = 1; index <= rule.occurrences; index += 1) {
    const nextStart = occurrenceStart(start, rule, index)
    payloads.push({
      ...base,
      start: format(nextStart),
      end: end === null ? '' : format(nextStart + (end - start)),
      deadline: deadline === null ? '' : format(nextStart + (deadline - start)),
    })
  }
  return {payloads, error: null}
}

export type DraftPoster = (payload: DraftPayload) => Promise<unknown>

/** Creates drafts one by one and stops at the first failure, reporting exactly how many exist. */
export async function createDrafts(post: DraftPoster, payloads: DraftPayload[]): Promise<{created: number; error: string | null}> {
  let created = 0
  for (const payload of payloads) {
    try { await post(payload) } catch (failure) {
      return {created, error: failure instanceof Error ? failure.message : 'A draft could not be created'}
    }
    created += 1
  }
  return {created, error: null}
}
