/** Before payment nobody knows whether the phone will be SMS-confirmed, so the bid card promises only a number. */
export function bidContactLine(kind:'provider'|'driver'):string{
  return `After payment: ${kind==='driver'?"the assigned driver's":"the truck owner's"} phone number. You will see whether it was confirmed by SMS.`
}
const BODIES:Record<string,string>={closed:'Closed body',open:'Open body',container:'Container',flatbed:'Flatbed',tanker:'Tanker',trailer:'Trailer'}
export function bodyTypeLabel(value:string|null|undefined):string{
  if(!value)return 'Truck'
  if(BODIES[value])return BODIES[value]
  const words=value.replaceAll('_',' ')
  return words.charAt(0).toUpperCase()+words.slice(1)
}
