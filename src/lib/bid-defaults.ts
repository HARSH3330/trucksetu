import {dateTime} from './demand-types'
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

type PickupWindow=DemandWindow&{latest_pickup_at:string}

/** The server refuses a bid whose pickup is outside the customer's pickup window or whose delivery is after the deadline; say which one before submitting. */
export function bidDateProblems(demand:PickupWindow,pickup:string,delivery:string){
  const time=(value:string)=>value?new Date(value).getTime():NaN
  const p=time(pickup),d=time(delivery)
  const pickupProblem=Number.isFinite(p)&&(p<time(demand.earliest_pickup_at)||p>time(demand.latest_pickup_at))
    ?`Pickup must be between ${dateTime(demand.earliest_pickup_at)} and ${dateTime(demand.latest_pickup_at)}, as the customer asked.`:null
  const deliveryProblem=!Number.isFinite(d)?null
    :d>time(demand.delivery_deadline_at)?`Delivery must be by ${dateTime(demand.delivery_deadline_at)}, the customer's deadline.`
    :Number.isFinite(p)&&d<=p?'Delivery must be after pickup.':null
  return {pickup:pickupProblem,delivery:deliveryProblem}
}
