import type {CurrentUser} from './api'
import type {View} from './routes'

export function defaultDestination(user:CurrentUser|null):'home'|'admin'|'dashboard'|'trips' {
  if(!user)return 'home'
  if(user.roles.some(role=>role==='admin'||role==='superadmin'))return 'admin'
  if(user.roles.some(role=>role==='provider'||role==='fleet_owner'))return 'dashboard'
  if(user.roles.includes('driver'))return 'trips'
  return user.roles.includes('customer')?'dashboard':'home'
}

export type MenuRole='visitor'|'customer'|'provider'|'driver'|'admin'

/** The most privileged role decides the menu, so an admin never sees customer links. */
export function menuRole(roles:string[]|null|undefined):MenuRole{
  if(!roles)return 'visitor'
  if(roles.some(role=>role==='admin'||role==='superadmin'))return 'admin'
  if(roles.some(role=>role==='provider'||role==='fleet_owner'))return 'provider'
  if(roles.includes('driver'))return 'driver'
  return 'customer'
}

const MENUS:Record<MenuRole,[View,string][]>={
  visitor:[['home','Home'],['ship','Post requirement'],['requirements','My requirements'],['pricing','Price estimate'],['support','Help']],
  customer:[['home','Home'],['ship','Post requirement'],['requirements','My requirements'],['bookings','Bookings & trips'],['pricing','Price estimate'],['support','Help']],
  provider:[['loads','Find loads'],['dashboard','My bids'],['fleet','Fleet & drivers'],['bookings','Bookings & trips'],['kyc','Verification'],['support','Help']],
  driver:[['trips','My trips'],['support','Help']],
  admin:[['admin','Control centre'],['vehicle-review','Vehicle approvals'],['kyc','Verification'],['support','Help']],
}

const MOBILE:Record<MenuRole,View[]>={
  visitor:['home','ship','requirements','pricing'],
  customer:['home','ship','requirements','bookings'],
  provider:['loads','dashboard','fleet','bookings'],
  driver:['trips','support'],
  admin:['admin','vehicle-review','kyc'],
}

export function menuFor(roles:string[]|null|undefined):[View,string][]{return MENUS[menuRole(roles)]}

export function mobileMenuFor(roles:string[]|null|undefined):[View,string][]{
  const role=menuRole(roles),labels=new Map(MENUS[role])
  return MOBILE[role].map(view=>[view,labels.get(view)||view])
}
