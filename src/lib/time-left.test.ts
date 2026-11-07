import {expect,it} from 'vitest'
import {timeLeft} from './time-left'

const now=new Date('2026-11-08T10:00:00Z')
const at=(minutes:number)=>new Date(now.getTime()+minutes*60000).toISOString()

it('says how long is left in hours and minutes',()=>{
  expect(timeLeft(at(200),now)).toBe('3 h 20 min left')
  expect(timeLeft(at(45),now)).toBe('45 min left')
  expect(timeLeft(at(0.5),now)).toBe('less than a minute left')
  expect(timeLeft(at(60*50),now)).toBe('2 days 2 h left')
})
it('says when time has run out',()=>{
  expect(timeLeft(at(-5),now)).toBe('expired')
  expect(timeLeft('not a date',now)).toBe('')
})
