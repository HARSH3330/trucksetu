import {useMemo, useState} from 'react'
import {apiFetch} from '../lib/api'
import {createDrafts, MAX_EVERY, MAX_OCCURRENCES, planRecurringDrafts, type DraftPayload, type Frequency} from '../lib/recurrence'

type Props = {base: DraftPayload; label: string; existingDrafts: number; onDone: (message: string) => void; onClose: () => void}
const UNIT: Record<Frequency, string> = {daily: 'day(s)', weekly: 'week(s)', monthly: 'month(s)'}

export default function RecurrencePanel({base, label, existingDrafts, onDone, onClose}: Props) {
  const [frequency, setFrequency] = useState<Frequency>('weekly')
  const [every, setEvery] = useState(1)
  const [occurrences, setOccurrences] = useState(4)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const plan = useMemo(() => planRecurringDrafts(base, {frequency, every, occurrences}, existingDrafts), [base, frequency, every, occurrences, existingDrafts])

  async function create() {
    if (plan.error || busy) return
    setBusy(true); setError('')
    const result = await createDrafts(payload => apiFetch('/demands/drafts', {method: 'POST', body: JSON.stringify({payload})}), plan.payloads)
    setBusy(false)
    if (result.error) {
      const failure = `${result.created} of ${plan.payloads.length} drafts were created before this failed: ${result.error}`
      if (result.created) onDone(`${failure}. Review the created drafts under Saved drafts.`)
      else setError(failure)
      return
    }
    onDone(`${result.created} draft(s) created for ${label}. Review each one and publish it yourself; nothing was published automatically.`)
  }

  return <section className="connection-panel" aria-label="Repeat requirement">
    <h2>Repeat this requirement</h2>
    <p>This creates drafts with later pickup dates. Nothing is published, no bids are requested and no fee is charged until you review and publish each draft.</p>
    <label>Repeat every<input type="number" min={1} max={MAX_EVERY} value={every} onChange={e => setEvery(Number(e.target.value))} /></label>
    <label>Unit<select value={frequency} onChange={e => setFrequency(e.target.value as Frequency)}>{(Object.keys(UNIT) as Frequency[]).map(key => <option key={key} value={key}>{key === 'daily' ? 'Day(s)' : key === 'weekly' ? 'Week(s)' : 'Month(s)'}</option>)}</select></label>
    <label>Number of copies<input type="number" min={1} max={MAX_OCCURRENCES} value={occurrences} onChange={e => setOccurrences(Number(e.target.value))} /></label>
    {plan.error ? <p role="alert">{plan.error}</p> : <>
      <p>New pickup start times (every {every} {UNIT[frequency]}):</p>
      <ul>{plan.payloads.map((payload, index) => <li key={index}>{new Date(String(payload.start)).toLocaleString('en-IN', {dateStyle: 'medium', timeStyle: 'short'})}</li>)}</ul>
    </>}
    {error && <p role="alert">{error}</p>}
    <button className="secondary" onClick={onClose} disabled={busy}>Cancel</button>
    <button onClick={() => void create()} disabled={Boolean(plan.error) || busy}>{busy ? 'Creating drafts…' : `Create ${plan.error ? '' : plan.payloads.length} draft(s)`}</button>
  </section>
}
