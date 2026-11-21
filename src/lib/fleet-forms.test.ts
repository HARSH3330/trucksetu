import {describe,expect,it} from 'vitest'
import {ApiError} from './api'
import {driverLinkError,payloadProblem} from './fleet-forms'

const mini={name:'Mini truck, 7–8 ft (Tata Ace class)',max_capacity_tonnes:'1.000'}

describe('vehicle form',()=>{
  it('says before submitting when the payload is above the chosen category limit',()=>{
    expect(payloadProblem(mini,'10')).toBe('Mini truck, 7–8 ft (Tata Ace class) carries up to 1 t. Choose a larger vehicle category or enter a payload of 1 t or less.')
    expect(payloadProblem(mini,'1')).toBeNull()
    expect(payloadProblem(mini,'0.5')).toBeNull()
    expect(payloadProblem(undefined,'10')).toBeNull()
    expect(payloadProblem(mini,'')).toBeNull()
  })
})

describe('driver link form',()=>{
  it('explains what to do when the email is not a driver account',()=>{
    expect(driverLinkError(new ApiError(404,'No verified driver account uses this email.'))).toBe('No driver account uses this email. Ask the driver to sign up on TransivoX as a driver with this email and complete driver verification, then link them here.')
  })
  it('explains that the driver still needs verification',()=>{
    expect(driverLinkError(new ApiError(403,"This driver's verification must be approved before you can link them."))).toBe('This driver has not been verified yet. They must finish driver verification before you can link them.')
  })
  it('keeps other server messages as they are',()=>{
    expect(driverLinkError(new ApiError(409,'This driving licence number is already registered.'))).toBe('This driving licence number is already registered.')
    expect(driverLinkError('boom')).toBe('Driver could not be linked. Try again.')
  })
})
