import {describe,it,expect} from 'vitest'
import {locationFromFields,clearLocation,moveLocation,confirmLocation} from './demand-location'
describe('private demand map state',()=>{
 it('never invents coordinates for a manual address',()=>{expect(locationFromFields({pickup_lat:'',pickup_lng:'',pickup_pin_confirmed:true},'pickup')).toBeNull()})
 it('keeps exact zero coordinates and rejects partial/nonfinite/out of range',()=>{expect(locationFromFields({pickup_lat:'0',pickup_lng:'0',pickup_pin_confirmed:true},'pickup')).toEqual({lat:0,lng:0});for(const p of [{pickup_lat:'0',pickup_lng:''},{pickup_lat:'NaN',pickup_lng:'4'},{pickup_lat:'91',pickup_lng:'4'}])expect(locationFromFields({...p,pickup_pin_confirmed:true},'pickup')).toBeNull()})
 it('address editing clears stale pin',()=>{expect(clearLocation('pickup')).toEqual({pickup_lat:'',pickup_lng:'',pickup_pin_confirmed:true})})
 it('pin movement requires address confirmation before submission',()=>{const p=moveLocation('pickup',{lat:28.61,lng:77.2});expect(p.pickup_pin_confirmed).toBe(false);expect(locationFromFields(p,'pickup')).toBeNull();expect(locationFromFields({...p,...confirmLocation('pickup')},'pickup')).toEqual({lat:28.61,lng:77.2})})
})
