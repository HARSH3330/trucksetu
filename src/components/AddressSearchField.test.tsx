import React from 'react'
import {renderToStaticMarkup} from 'react-dom/server'
import {expect,it} from 'vitest'
import AddressSearchField from './AddressSearchField'
import LocationMap from './LocationMap'

it('is a labelled combobox that keeps manual typing available',()=>{
  const html=renderToStaticMarkup(<AddressSearchField id="pickup-address" label="Pickup address — private" value="" onType={()=>{}} onPick={()=>{}} required/>)
  expect(html).toContain('<label for="pickup-address">Pickup address — private</label>')
  expect(html).toMatch(/<input(?=[^>]*id="pickup-address")(?=[^>]*role="combobox")(?=[^>]*aria-autocomplete="list")(?=[^>]*aria-expanded="false")(?=[^>]*required="")[^>]*>/)
  expect(html).not.toContain('role="listbox"')
})
it('shows no map until a place has been chosen',()=>{
  expect(renderToStaticMarkup(<LocationMap points={{pickup:null,destination:null}}/>)).toBe('')
  expect(renderToStaticMarkup(<LocationMap points={{pickup:{lat:28.6,lng:77.2},destination:null}}/>)).toContain('aria-label="Map of the chosen locations"')
})
