import React from 'react'
import {renderToStaticMarkup} from 'react-dom/server'
import {expect,it} from 'vitest'
import StopsEditor from './StopsEditor'
import {writeStops} from '../lib/stops'

it('offers an Add a stop button when there are no stops',()=>{
  const html=renderToStaticMarkup(<StopsEditor value="" onChange={()=>{}}/>)
  expect(html).toContain('Stops on the way')
  expect(html).toMatch(/<button[^>]*>.*Add a stop<\/button>/)
})
it('shows each stop with its own address search, activity and remove button',()=>{
  const html=renderToStaticMarkup(<StopsEditor value={writeStops([{address:'Saket, Delhi',activity:'drop',note:''},{address:'Okhla, Delhi',activity:'pickup',note:'4 cartons'}])} onChange={()=>{}}/>)
  expect(html).toContain('<label for="stop-2-address">Stop 2 address</label>')
  expect(html).toContain('aria-label="Remove stop 1"')
  expect(html).toContain('Add another stop')
})
