export function tripReadPath(roles:string[]):'/bookings'|'/drivers/me/trips' {
  return roles.includes('driver')&&!roles.some(role=>['provider','fleet_owner','admin','superadmin'].includes(role))?'/drivers/me/trips':'/bookings'
}
export function canOperateTrips(roles:string[]):boolean {return roles.some(role=>['driver','provider','fleet_owner','admin','superadmin'].includes(role))}

export function canRunTripActions(bookingStatus:string,available?:boolean):boolean {return available!==false&&!['connection_fee_pending','cancelled','disputed'].includes(bookingStatus)}
