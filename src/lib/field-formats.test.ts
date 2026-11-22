import {describe,expect,it} from 'vitest'
import {FORMATS,formatWarning} from './field-formats'

describe('field formats match the server rules',()=>{
  it('stays quiet while the field is empty or valid',()=>{
    expect(formatWarning(FORMATS.registration,'')).toBeNull()
    expect(formatWarning(FORMATS.registration,'MH 12 AB 1234')).toBeNull()
    expect(formatWarning(FORMATS.licence,'MH12-20110012345')).toBeNull()
    expect(formatWarning(FORMATS.panLastFour,'234F')).toBeNull()
    expect(formatWarning(FORMATS.gstin,'22AAAAA0000A1Z5')).toBeNull()
    expect(formatWarning(FORMATS.invoiceGstin,'22AAAAA0000A1Z5')).toBeNull()
    expect(formatWarning(FORMATS.mobile,'+91 98765 43210')).toBeNull()
    expect(formatWarning(FORMATS.mobile,'98765-43210')).toBeNull()
    expect(formatWarning(FORMATS.otpMobile,'+919876543210')).toBeNull()
  })
  it('warns when the typed value would be refused',()=>{
    expect(formatWarning(FORMATS.registration,'MH12/AB')).toMatch(/letters, numbers, spaces and hyphens/)
    expect(formatWarning(FORMATS.registration,'MH1')).toMatch(/at least 5/)
    expect(formatWarning(FORMATS.licence,'DL#123456')).toMatch(/letters, numbers, spaces and hyphens/)
    expect(formatWarning(FORMATS.panLastFour,'23F')).toMatch(/exactly 4/)
    expect(formatWarning(FORMATS.gstin,'22AAAAA0000A1Z')).toMatch(/15 characters/)
    expect(formatWarning(FORMATS.invoiceGstin,'22AAAAA0000A0Z5')).toMatch(/15 characters/)
    expect(formatWarning(FORMATS.mobile,'12345')).toMatch(/mobile/)
    expect(formatWarning(FORMATS.otpMobile,'+91 98765 43210')).toMatch(/without spaces/)
  })
})
