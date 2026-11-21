import {renderToStaticMarkup} from 'react-dom/server'
import {expect,it} from 'vitest'
import DemandPins,{mapLink} from './DemandPins'

it('shows the exact pickup and drop address with a link to each pin',()=>{
  const html=renderToStaticMarkup(<DemandPins pickup_address="Gate 3, Okhla Phase 2, New Delhi 110020" destination_address="Plot 14, Sector 63, Noida 201301" pickup_location={{lat:28.613901,lng:77.209006}} destination_location={null}/>)
  expect(html).toContain('Pickup: Gate 3, Okhla Phase 2, New Delhi 110020')
  expect(html).toContain('Drop: Plot 14, Sector 63, Noida 201301')
  expect(html).toContain('href="https://www.google.com/maps/search/?api=1&amp;query=28.613901,77.209006"')
  expect(html).toContain('rel="noopener noreferrer"')
  expect(html).toContain('Open pickup pin')
  expect(html).toContain('No drop pin; use the address')
})

it('renders nothing when the viewer is not allowed the exact location',()=>{
  expect(renderToStaticMarkup(<DemandPins/>)).toBe('')
})

it('builds a map link only from valid coordinates',()=>{
  expect(mapLink({lat:28.5,lng:77.25})).toBe('https://www.google.com/maps/search/?api=1&query=28.500000,77.250000')
  expect(mapLink({lat:91,lng:0})).toBeNull()
  expect(mapLink(null)).toBeNull()
})
