import {describe, expect, it} from 'vitest'
import {checkoutSentence, taxSentence} from './fee-copy'
import type {MarketplaceConfig} from './demand-types'

const base = (over: object = {}, fee: object = {}) => ({real_checkout_available: false, fee: {amount: '99.00', total: '99.00', tax_amount: '15.10', tax_rate: '0.18', tax_confirmed: false, ...fee}, ...over}) as unknown as MarketplaceConfig

describe('fee copy follows server state', () => {
  it('says the rate is unconfirmed only while it is unconfirmed', () => {
    expect(taxSentence(base())).toMatch(/still requires confirmation/)
    expect(taxSentence(base({}, {tax_confirmed: true}))).toBe('Tax: 18% — ₹15.10 included; total ₹99.00.')
  })
  it('formats tax rates without floating-point noise', () => {
    expect(taxSentence(base({}, {tax_confirmed: true, tax_rate: '0.28'}))).toBe('Tax: 28% — ₹15.10 included; total ₹99.00.')
    expect(taxSentence(base({}, {tax_confirmed: true, tax_rate: '0.125'}))).toBe('Tax: 12.5% — ₹15.10 included; total ₹99.00.')
  })
  it('handles missing configuration honestly', () => {
    expect(taxSentence(null)).toMatch(/pending server configuration/)
    expect(taxSentence(base({}, {tax_amount: null}))).toMatch(/pending server configuration/)
  })
  it('only claims checkout is disabled when it is', () => {
    expect(checkoutSentence(base())).toBe('Real checkout is disabled.')
    expect(checkoutSentence(base({real_checkout_available: true}))).not.toMatch(/disabled/)
    expect(checkoutSentence(null)).toBe('Real checkout is disabled.')
  })
})
