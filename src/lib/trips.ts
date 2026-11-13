export function tripReadPath(roles:string[]):'/bookings'|'/drivers/me/trips' {
  return roles.includes('driver')&&!roles.some(role=>['provider','fleet_owner','admin','superadmin'].includes(role))?'/drivers/me/trips':'/bookings'
}
export function canOperateTrips(roles:string[]):boolean {return roles.some(role=>['driver','provider','fleet_owner','admin','superadmin'].includes(role))}

export function canRunTripActions(bookingStatus:string,available?:boolean):boolean {return available!==false&&!['connection_fee_pending','cancelled','disputed'].includes(bookingStatus)}

const TRANSITIONS:Record<string,string[]>={driver_assigned:['heading_to_pickup'],heading_to_pickup:['arrived_at_pickup','on_hold'],pickup_verified:['loaded'],loaded:['in_transit'],in_transit:['at_stop','arrived_at_destination','on_hold'],at_stop:['in_transit'],delivery_verified:['delivered'],delivered:['completed'],on_hold:['heading_to_pickup','in_transit']}
/** Next status updates to offer; a stop update is offered only when the load has stops. */
export function tripActions(status:string,stopCount:number|undefined):string[]{
  const next=TRANSITIONS[status]||[]
  return stopCount===0?next.filter(value=>value!=='at_stop'):next
}
