type DemandWindow={earliest_pickup_at:string;delivery_deadline_at:string}
type Truck={id:string;status:string;document_eligible_today:boolean}

const DAY=24*3600000

/** "YYYY-MM-DDTHH:mm" in the viewer's local time, as datetime-local inputs expect. */
export function localInput(value:string):string{
  const date=new Date(value)
  return Number.isFinite(date.getTime())?new Date(date.getTime()-date.getTimezoneOffset()*60000).toISOString().slice(0,16):''
}

export const eligibleTrucks=<T extends Truck>(trucks:T[])=>trucks.filter(truck=>truck.status==='approved'&&truck.document_eligible_today)

/** Starting values for a new bid; every field stays editable. */
export function bidDefaults(demand:DemandWindow,trucks:Truck[],now:Date=new Date()){
  const pickup=new Date(demand.earliest_pickup_at).getTime()
  const expiry=Math.min(now.getTime()+DAY,pickup)
  const usable=eligibleTrucks(trucks)
  return {
    pickup:localInput(demand.earliest_pickup_at),
    delivery:localInput(demand.delivery_deadline_at),
    // The server requires expiry after now and no later than pickup.
    expiry:expiry>now.getTime()?localInput(new Date(expiry).toISOString()):'',
    vehicle:usable.length===1?usable[0].id:'',
  }
}
