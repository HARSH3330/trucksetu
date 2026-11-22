import {renderToStaticMarkup} from 'react-dom/server'
import {describe,expect,it} from 'vitest'
import {BidRow,sortBids} from './DemandWorkspace'
import LivePricing from './LivePricing'
import {PublicSupport} from './PublicInformation'
import type {DemandBid} from '../lib/demand-types'

const bid=(id:string,amount:string,pickup:string)=>({id,request_id:'r',version:1,request_revision:1,status:'active',provider_name:'Fictional Fleet '+id,provider_verified:true,amount,currency:'INR',pickup_at:pickup,delivery_at:'2026-11-25T10:00:00Z',expires_at:'2099-01-01T00:00:00Z',inclusions:'Loading, tolls',exclusions:'None',notes:null,contact_kind:'provider',vehicle:{body_type:'closed',payload_tonnes:'9',volume_m3:'30'}}) as unknown as DemandBid

describe('bid comparison for small shippers',()=>{
  it('sorts by lowest price or earliest pickup without changing the bids',()=>{
    const bids=[bid('a','25000','2026-11-23T05:00:00Z'),bid('b','18000','2026-11-24T05:00:00Z'),bid('c','21000','2026-11-22T05:00:00Z')]
    expect(sortBids(bids,'price').map(x=>x.id)).toEqual(['b','c','a'])
    expect(sortBids(bids,'pickup').map(x=>x.id)).toEqual(['c','a','b'])
    expect(bids.map(x=>x.id)).toEqual(['a','b','c'])
  })
  it('shows the price you pay first and keeps the fine print behind Show details',()=>{
    const html=renderToStaticMarkup(<BidRow bid={bid('a','25000','2026-11-23T05:00:00Z')} now={new Date('2026-11-22T00:00:00Z')} canChoose onChoose={()=>{}}/>)
    expect(html).toContain("Truck owner&#x27;s price")
    expect(html).toContain('You pay this directly to the truck owner')
    expect(html).toMatch(/<details[^>]*><summary>Show details<\/summary>.*Included:.*Excluded:/s)
    expect(html).toMatch(/<button[^>]*>Choose this bid<\/button>/)
  })
})

describe('advisory estimate versus the price you pay',()=>{
  it('says the estimate is not the price you pay',()=>{
    const html=renderToStaticMarkup(<LivePricing/>)
    expect(html).toContain('TransivoX estimate (advisory)')
    expect(html).toContain('not the price you pay')
  })
})

describe('help page',()=>{
  it('puts ways to get help first, with a direct trip-problem link and emergency advice',()=>{
    const html=renderToStaticMarkup(<PublicSupport/>)
    expect(html.indexOf('Get help')).toBeLessThan(html.indexOf('What verification means'))
    expect(html).toContain('href="#trust"')
    expect(html).toContain('Report a problem on a trip')
    expect(html).toContain('call 112')
    expect(html).not.toContain('WhatsApp')
    expect(html).not.toContain('tel:')
  })
  it('shows phone and WhatsApp only when a support number is configured',()=>{
    const html=renderToStaticMarkup(<PublicSupport phone="+91 98765 43210" whatsapp="919876543210"/>)
    expect(html).toContain('href="tel:+919876543210"')
    expect(html).toContain('href="https://wa.me/919876543210"')
  })
})
