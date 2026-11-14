import {describe, expect, it} from 'vitest'
import {buildVehiclePatch, formFromVehicle, reviewResetWarning, type EditableVehicle} from './vehicleEdit'

const vehicle: EditableVehicle = {
  vehicle_category_id: 'cat-1', body_type: 'closed', maximum_payload_tonnes: '9.000', maximum_volume_m3: '34.560',
  internal_length_m: '6.000', internal_width_m: '2.400', internal_height_m: '2.400',
  permit_territories: ['KA', 'MH'], service_areas: ['Bengaluru'],
}

describe('vehicle edit patch', () => {
  it('sends nothing for an untouched form, so approval is never reset by opening the editor', () => {
    expect(buildVehiclePatch(vehicle, formFromVehicle(vehicle))).toEqual({})
  })
  it('treats equivalent numeric strings as unchanged', () => {
    expect(buildVehiclePatch(vehicle, {...formFromVehicle(vehicle), payload: '9', length: '6'})).toEqual({})
  })
  it('sends only the changed fields with numbers and trimmed lists', () => {
    const form = {...formFromVehicle(vehicle), payload: '8.5', areas: ' Bengaluru , Mysuru ,, '}
    expect(buildVehiclePatch(vehicle, form)).toEqual({maximum_payload_tonnes: 8.5, service_areas: ['Bengaluru', 'Mysuru']})
  })
  it('warns honestly about re-review only when something changed on a reviewed vehicle', () => {
    expect(reviewResetWarning('approved', {})).toBe('No changes to save.')
    expect(reviewResetWarning('approved', {body_type: 'open'})).toMatch(/manual review/)
    expect(reviewResetWarning('pending', {body_type: 'open'})).not.toMatch(/back to manual review/)
  })
})
