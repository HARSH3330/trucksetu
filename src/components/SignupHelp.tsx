import {Check} from 'lucide-react'

export const ROLE_CHOICES=[
  {value:'customer',label:'Customer — I need goods moved',help:'Post what you need moved, compare bids from verified truck owners and choose one.'},
  {value:'provider',label:'Truck owner — I bid on loads',help:'You own a truck or a few trucks and bid on customer loads yourself.'},
  {value:'fleet_owner',label:'Fleet owner — I manage trucks and drivers',help:'You manage several trucks and drivers, bid on loads and assign your drivers.'},
  {value:'driver',label:'Driver — I drive for a truck owner',help:'You drive for a truck owner, who links you to their trips after you sign up.'},
] as const

/** The same four rules the server enforces on sign-up. */
export function passwordChecks(password:string){
  return [
    {label:'At least 10 characters',met:password.length>=10},
    {label:'An uppercase letter',met:/[A-Z]/.test(password)},
    {label:'A lowercase letter',met:/[a-z]/.test(password)},
    {label:'A number',met:/\d/.test(password)},
  ]
}

export function PasswordChecklist({password}:{password:string}){
  return <ul className="password-checklist" aria-live="polite">
    {passwordChecks(password).map(check=><li key={check.label} className={check.met?'met':undefined}>
      <span className="visually-hidden">{check.met?'Met: ':'Not yet: '}</span><span aria-hidden="true">{check.met?<Check/>:'○'}</span>{check.label}
    </li>)}
  </ul>
}
