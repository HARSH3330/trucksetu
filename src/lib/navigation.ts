import type {CurrentUser} from './api'

export function defaultDestination(user:CurrentUser|null):'home'|'admin'|'dashboard'|'trips' {
  if(!user)return 'home'
  if(user.roles.some(role=>role==='admin'||role==='superadmin'))return 'admin'
  if(user.roles.some(role=>role==='provider'||role==='fleet_owner'))return 'dashboard'
  if(user.roles.includes('driver'))return 'trips'
  return user.roles.includes('customer')?'dashboard':'home'
}
