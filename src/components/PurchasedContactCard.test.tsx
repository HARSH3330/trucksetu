import {renderToStaticMarkup} from 'react-dom/server'
import {describe,expect,it} from 'vitest'
import PurchasedContactCard from './PurchasedContactCard'

const base={state:'unlocked' as const,contact_kind:'provider' as const,contact_name:'Fictional Fleet',phone:'+918123456789',email:'fleet@example.com',notice:'Purchased for this booking.'}

describe('purchased contact card',()=>{
  it('says plainly when the phone was not verified by SMS and shows the verified email',()=>{
    const html=renderToStaticMarkup(<PurchasedContactCard contact={{...base,phone_verified:false}}/>)
    expect(html).toContain('href="tel:+918123456789"')
    expect(html).toContain('Phone not verified by SMS')
    expect(html).toContain('href="mailto:fleet@example.com"')
    expect(html).toContain('Email verified')
  })
  it('marks an SMS-verified phone as verified',()=>{
    const html=renderToStaticMarkup(<PurchasedContactCard contact={{...base,phone_verified:true}}/>)
    expect(html).toContain('Phone verified by SMS')
    expect(html).not.toContain('not verified')
  })
})
