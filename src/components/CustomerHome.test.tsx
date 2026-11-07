import React from 'react'
import {renderToStaticMarkup} from 'react-dom/server'
import {expect,it} from 'vitest'
import {HomeFeeNotice} from './CustomerHome'
import type {MarketplaceConfig} from '../lib/demand-types'

const config=(fee:object,over:object={})=>({real_checkout_available:true,fee:{amount:'99.00',total:'99.00',tax_amount:'15.10',tax_rate:'0.18',...fee},...over}) as unknown as MarketplaceConfig

it('states the confirmed tax and live checkout from server settings',()=>{
  const html=renderToStaticMarkup(<HomeFeeNotice config={config({tax_confirmed:true})}/>)
  expect(html).toContain('Tax: 18% — ₹15.10 included; total ₹99.00.')
  expect(html).not.toContain('requires confirmation')
  expect(html).not.toContain('Real checkout is disabled')
})
it('only says checkout is disabled or tax unconfirmed when the server says so',()=>{
  const html=renderToStaticMarkup(<HomeFeeNotice config={config({tax_confirmed:false},{real_checkout_available:false})}/>)
  expect(html).toContain('still requires confirmation')
  expect(html).toContain('Real checkout is disabled.')
})
