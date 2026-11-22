import {money,type Fee} from './demand-types'

const paise=(value:string)=>Math.round(Number(value)*100)
const rupees=(value:number)=>(value/100).toFixed(2)

/** Rows that always add up: base + tax = total. Amounts are in paise to avoid floating-point drift. */
export function feeRows(fee:Pick<Fee,'amount'|'total'|'currency'|'tax_treatment'|'tax_amount'|'tax_confirmed'|'tax_rate'>):[string,string][]{
  const total:[string,string]=['Total connection payment',money(fee.total,fee.currency)]
  if(fee.tax_treatment==='undecided'||fee.tax_amount===null)return [['Connection fee',money(fee.amount,fee.currency)],['Tax','Pending confirmation'],total]
  const tax=paise(fee.tax_amount),base=fee.tax_treatment==='included'?paise(fee.amount)-tax:paise(fee.amount)
  const rate=base>0?` (${Math.round(tax*100/base)}%)`:''
  return [['Connection fee before tax',money(rupees(base),fee.currency)],[`${fee.tax_confirmed?'Tax':'Proposed tax'}${rate}`,money(fee.tax_amount,fee.currency)],total]
}
