import type {MarketplaceConfig} from './demand-types'

/** Customer-facing fee copy must follow the server's real state, never fixed claims. */
export function taxSentence(config: MarketplaceConfig | null): string {
  const fee = config?.fee
  if (!fee?.tax_amount) return 'Tax is pending server configuration and confirmation.'
  const rate = fee.tax_rate ? `${Number((Number(fee.tax_rate) * 100).toFixed(4))}% — ` : ''
  if (fee.tax_confirmed) return `Tax: ${rate}₹${fee.tax_amount} included; total ₹${fee.total}.`
  return `Proposed tax: ${rate}₹${fee.tax_amount}; total ₹${fee.total}. The applicable rate still requires confirmation.`
}

export function checkoutSentence(config: MarketplaceConfig | null): string {
  return config?.real_checkout_available ? 'Checkout opens after you select a provider’s bid.' : 'Real checkout is disabled.'
}
