export type EditableVehicle = {
  vehicle_category_id: string; body_type: string; maximum_payload_tonnes: string; maximum_volume_m3: string
  internal_length_m: string; internal_width_m: string; internal_height_m: string
  permit_territories: string[]; service_areas: string[]
}
export type VehicleEditForm = {
  category: string; body: string; payload: string; length: string; width: string; height: string; volume: string
  territories: string; areas: string
}

const list = (value: string) => value.split(',').map(item => item.trim()).filter(Boolean)
const same = (a: string[], b: string[]) => a.length === b.length && a.every((item, index) => item === b[index])
const num = (value: string) => Number(value)

export function formFromVehicle(vehicle: EditableVehicle): VehicleEditForm {
  return {
    category: vehicle.vehicle_category_id, body: vehicle.body_type, payload: vehicle.maximum_payload_tonnes,
    length: vehicle.internal_length_m, width: vehicle.internal_width_m, height: vehicle.internal_height_m,
    volume: vehicle.maximum_volume_m3, territories: vehicle.permit_territories.join(', '), areas: vehicle.service_areas.join(', '),
  }
}

/** Only fields the provider actually changed are sent, so an untouched form never resets an approval. */
export function buildVehiclePatch(original: EditableVehicle, form: VehicleEditForm): Record<string, unknown> {
  const patch: Record<string, unknown> = {}
  if (form.category !== original.vehicle_category_id) patch.vehicle_category_id = form.category
  if (form.body !== original.body_type) patch.body_type = form.body
  if (num(form.payload) !== num(original.maximum_payload_tonnes)) patch.maximum_payload_tonnes = num(form.payload)
  if (num(form.length) !== num(original.internal_length_m)) patch.internal_length_m = num(form.length)
  if (num(form.width) !== num(original.internal_width_m)) patch.internal_width_m = num(form.width)
  if (num(form.height) !== num(original.internal_height_m)) patch.internal_height_m = num(form.height)
  if (num(form.volume) !== num(original.maximum_volume_m3)) patch.maximum_volume_m3 = num(form.volume)
  if (!same(list(form.territories), original.permit_territories)) patch.permit_territories = list(form.territories)
  if (!same(list(form.areas), original.service_areas)) patch.service_areas = list(form.areas)
  return patch
}

export function reviewResetWarning(status: string, patch: Record<string, unknown>): string {
  if (!Object.keys(patch).length) return 'No changes to save.'
  return status === 'approved' || status === 'rejected'
    ? 'Saving sends this vehicle back to manual review. It cannot take new assignments until an administrator approves it again.'
    : 'Saving updates the vehicle while it waits for review.'
}
