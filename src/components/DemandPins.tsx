type Pin={lat:number;lng:number}|null|undefined

/** Google Maps link for a saved pin; null when there is no valid pin. */
export function mapLink(pin:Pin){
  if(!pin||!Number.isFinite(pin.lat)||!Number.isFinite(pin.lng)||Math.abs(pin.lat)>90||Math.abs(pin.lng)>180)return null
  return `https://www.google.com/maps/search/?api=1&query=${pin.lat.toFixed(6)},${pin.lng.toFixed(6)}`
}

/**
 * Exact pickup and drop for verified truck owners, admins and the customer (owner decision 2026-11-20).
 * The API omits these fields for everyone else, so nothing renders for them.
 */
export default function DemandPins({pickup_address,destination_address,pickup_location,destination_location}:{pickup_address?:string|null;destination_address?:string|null;pickup_location?:Pin;destination_location?:Pin}){
  if(!pickup_address&&!destination_address)return null
  const line=(label:string,name:string,address:string|null|undefined,pin:Pin)=>{
    const link=mapLink(pin)
    return <p className="demand-pin-line"><b>{label}: {address||'address not given'}</b>{link?<a href={link} target="_blank" rel="noopener noreferrer">Open {name} pin in Google Maps</a>:<small>No {name} pin; use the address</small>}</p>
  }
  return <div className="demand-pins" aria-label="Exact pickup and drop">
    {line('Pickup','pickup',pickup_address,pickup_location)}
    {line('Drop','drop',destination_address,destination_location)}
  </div>
}
