import {expect,it} from 'vitest'
import {bidContactLine,bodyTypeLabel} from './bid-copy'

it('never promises a verified phone before the customer pays',()=>{
  for(const kind of ['provider','driver'] as const){
    expect(bidContactLine(kind)).not.toMatch(/verified/i)
  }
  expect(bidContactLine('provider')).toBe("After payment: the truck owner's phone number. You will see whether it was confirmed by SMS.")
  expect(bidContactLine('driver')).toBe("After payment: the assigned driver's phone number. You will see whether it was confirmed by SMS.")
})
it('names truck bodies in plain words',()=>{
  expect(bodyTypeLabel('closed')).toBe('Closed body')
  expect(bodyTypeLabel('open')).toBe('Open body')
  expect(bodyTypeLabel('flatbed_trailer')).toBe('Flatbed trailer')
  expect(bodyTypeLabel(undefined)).toBe('Truck')
})
