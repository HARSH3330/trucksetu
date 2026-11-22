import {useState, type FormEvent} from 'react'
import {apiFetch, type VehicleCategory} from '../lib/api'
import {buildVehiclePatch, formFromVehicle, reviewResetWarning, type EditableVehicle, type VehicleEditForm as FormState} from '../lib/vehicleEdit'

type Props = {vehicle: EditableVehicle & {id: string; registration_number: string; status: string}; categories: VehicleCategory[]; onSaved: (message: string) => void; onCancel: () => void}

export default function VehicleEditForm({vehicle, categories, onSaved, onCancel}: Props) {
  const [form, setForm] = useState<FormState>(formFromVehicle(vehicle))
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const set = (key: keyof FormState, value: string) => setForm(current => ({...current, [key]: value}))
  const patch = buildVehiclePatch(vehicle, form)
  const changed = Object.keys(patch).length > 0

  async function submit(event: FormEvent) {
    event.preventDefault()
    if (!changed || busy) return
    setBusy(true); setError('')
    try {
      await apiFetch(`/carrier-vehicles/${vehicle.id}`, {method: 'PATCH', body: JSON.stringify(patch)})
      onSaved(vehicle.status === 'approved' || vehicle.status === 'rejected' ? 'Vehicle updated and sent back for manual review.' : 'Vehicle updated.')
    } catch (failure) {
      setError(failure instanceof Error ? failure.message : 'Vehicle could not be updated')
    } finally { setBusy(false) }
  }

  return <form className="panel fleet-form" onSubmit={submit} aria-label={`Edit vehicle ${vehicle.registration_number}`}>
    <h3>Edit {vehicle.registration_number}</h3>
    <p>Registration number and document expiry dates cannot be changed here. Replace documents from Private documents instead.</p>
    <label>Vehicle category<select value={form.category} onChange={e => set('category', e.target.value)}>{categories.map(item => <option value={item.id} key={item.id}>{item.name} · max {item.max_capacity_tonnes} t</option>)}</select></label>
    <label>Body type<select value={form.body} onChange={e => set('body', e.target.value)}><option value="closed">Closed</option><option value="open">Open</option><option value="container">Container</option></select></label>
    <label>Maximum payload (tonnes)<input required type="number" step="0.001" min="0.001" value={form.payload} onChange={e => set('payload', e.target.value)} /></label>
    <label>Internal length (m)<input required type="number" step="0.001" min="0.001" max="30" value={form.length} onChange={e => set('length', e.target.value)} /></label>
    <label>Internal width (m)<input required type="number" step="0.001" min="0.001" max="10" value={form.width} onChange={e => set('width', e.target.value)} /></label>
    <label>Internal height (m)<input required type="number" step="0.001" min="0.001" max="10" value={form.height} onChange={e => set('height', e.target.value)} /></label>
    <label>Maximum cargo volume (m³)<input required type="number" step="0.001" min="0.001" value={form.volume} onChange={e => set('volume', e.target.value)} /></label>
    <label>Permit territories (comma separated)<input required value={form.territories} onChange={e => set('territories', e.target.value)} /></label>
    <label>Service areas (comma separated)<input required value={form.areas} onChange={e => set('areas', e.target.value)} /></label>
    <p role="status">{reviewResetWarning(vehicle.status, patch)}</p>
    {error && <p role="alert">{error}</p>}
    <button disabled={!changed || busy}>{busy ? 'Saving…' : 'Save changes'}</button>
    <button type="button" className="secondary" onClick={onCancel} disabled={busy}>Cancel</button>
  </form>
}
