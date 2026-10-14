import {describe, expect, it} from 'vitest'
import {createIdentityTestPdf} from './pdf'

describe('identity test PDF', () => {
  it('creates a valid fictional PDF with an unmistakable warning', () => {
    const bytes = createIdentityTestPdf('Aadhaar', 'run-123')
    const text = bytes.toString('latin1')
    expect(text.startsWith('%PDF-1.4')).toBe(true)
    expect(text).toContain('NOT A REAL IDENTITY DOCUMENT')
    expect(text).toContain('Aadhaar')
    expect(text).toContain('%%EOF')
  })
})
