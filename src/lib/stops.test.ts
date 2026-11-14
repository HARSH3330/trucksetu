import {describe,expect,it} from 'vitest'
import {MAX_STOPS,readStops,stopsPayload,stopsProblem,writeStops} from './stops'

describe('stops on the way',()=>{
  it('round-trips through the text field used by drafts',()=>{
    const stops=[{address:'Okhla Phase 2, Delhi',activity:'pickup' as const,note:'4 cartons'}]
    expect(readStops(writeStops(stops))).toEqual(stops)
    expect(readStops('')).toEqual([])
    expect(readStops('not json')).toEqual([])
  })
  it('sends trimmed stops in order and skips empty rows',()=>{
    expect(stopsPayload([{address:' Saket, Delhi ',activity:'drop',note:''},{address:'  ',activity:'drop',note:''}]))
      .toEqual([{address:'Saket, Delhi',activity:'drop',instructions:null}])
  })
  it('explains what is wrong before publishing',()=>{
    expect(stopsProblem([{address:'ab',activity:'drop',note:''}])).toBe('Stop 1 needs a full address.')
    expect(stopsProblem([{address:'Saket, Delhi',activity:'drop',note:''}])).toBeNull()
    expect(MAX_STOPS).toBe(20)
  })
})
