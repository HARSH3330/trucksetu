import {expect,it} from 'vitest'
import {feeRows} from './fee-breakdown'

const included={version:'v1',amount:'99.00',total:'99.00',currency:'INR',basis:'booking',tax_treatment:'included',tax_amount:'15.10',tax_rate:'0.18',tax_confirmed:true}

it('shows a tax-included fee as base plus tax that adds up to the total',()=>{
  expect(feeRows(included)).toEqual([['Connection fee before tax','₹83.90'],['Tax (18%)','₹15.10'],['Total connection payment','₹99.00']])
})

it('takes the percentage from the amounts so a stale rate setting cannot contradict them',()=>{
  expect(feeRows({...included,tax_rate:'0.20'})[1]).toEqual(['Tax (18%)','₹15.10'])
})

it('calls the tax proposed only while it is unconfirmed',()=>{
  expect(feeRows({...included,tax_confirmed:false})[1]).toEqual(['Proposed tax (18%)','₹15.10'])
})

it('adds tax on top when it is charged in addition',()=>{
  expect(feeRows({...included,amount:'83.90',total:'99.00',tax_treatment:'additional'})).toEqual([['Connection fee before tax','₹83.90'],['Tax (18%)','₹15.10'],['Total connection payment','₹99.00']])
})

it('never invents a tax figure when tax is undecided',()=>{
  expect(feeRows({...included,tax_treatment:'undecided',tax_amount:null,total:'99.00'})).toEqual([['Connection fee','₹99.00'],['Tax','Pending confirmation'],['Total connection payment','₹99.00']])
})
