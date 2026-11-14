import {ApiError} from './api'

const tonnes=(value:number)=>`${Number(value.toFixed(3))} t`

/** The server rejects a payload above the category's safe limit; say so before the owner submits. */
export function payloadProblem(category:{name:string;max_capacity_tonnes:string}|undefined,payload:string):string|null{
  const limit=Number(category?.max_capacity_tonnes),value=Number(payload)
  if(!category||!payload||!Number.isFinite(limit)||!Number.isFinite(value)||value<=limit)return null
  return `${category.name} carries up to ${tonnes(limit)}. Choose a larger vehicle category or enter a payload of ${tonnes(limit)} or less.`
}

/** Turns the link-driver refusals into the next step the fleet owner can take. */
export function driverLinkError(error:unknown):string{
  if(error instanceof ApiError&&error.status===404)return 'No driver account uses this email. Ask the driver to sign up on TransivoX as a driver with this email and complete driver verification, then link them here.'
  if(error instanceof ApiError&&error.status===403&&/kyc|verif/i.test(error.message))return 'This driver has not been verified yet. They must finish driver verification before you can link them.'
  return error instanceof Error&&error.message?error.message:'Driver could not be linked. Try again.'
}
