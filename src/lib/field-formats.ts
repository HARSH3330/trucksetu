/** Fixed-format fields. Each rule mirrors the server's validation so the warning appears before the server refuses the value. */
export type FieldFormat={hint:string;check:(value:string)=>string|null}

const plateLike=(label:string,max:number):FieldFormat['check']=>value=>{
  if(!/^[A-Za-z0-9 -]+$/.test(value))return `Use only letters, numbers, spaces and hyphens in the ${label}.`
  if(value.length<5)return `The ${label} needs at least 5 characters.`
  if(value.length>max)return `The ${label} can have at most ${max} characters.`
  return null
}
const gstin=(pattern:RegExp):FieldFormat['check']=>value=>pattern.test(value)?null:'A GSTIN has 15 characters: 2-digit state code, 10-character PAN, entity number, Z, check character.'
const mobileDigits=/^\+?[1-9][0-9]{7,14}$/

export const FORMATS={
  registration:{hint:'Format: letters, numbers, spaces or hyphens, 5–30 characters. Example: MH 12 AB 1234',check:plateLike('registration number',30)},
  licence:{hint:'Format: letters, numbers, spaces or hyphens, 5–50 characters, as printed on the licence. Example: MH12 20110012345',check:plateLike('licence number',50)},
  panLastFour:{hint:'Format: the last 4 characters of the PAN, capital letters or numbers. Example: 234F',check:value=>/^[A-Z0-9]{4}$/.test(value)?null:'Enter exactly 4 capital letters or numbers.'},
  gstin:{hint:'Format: 15 characters. Example: 22AAAAA0000A1Z5',check:gstin(/^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z][A-Z0-9]Z[A-Z0-9]$/)},
  invoiceGstin:{hint:'Format: 15 characters. Example: 22AAAAA0000A1Z5',check:gstin(/^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z][1-9A-Z]Z[0-9A-Z]$/)},
  mobile:{hint:'Format: 10-digit mobile number, or with country code. Example: +91 98765 43210',check:value=>value.length<=25&&mobileDigits.test(value.replace(/[\s().-]/g,''))?null:'Enter a valid mobile number, for example +91 98765 43210.'},
  otpMobile:{hint:'Format: 10–15 digits without spaces, country code optional. Example: +919876543210',check:value=>/^\+?[0-9]{10,15}$/.test(value)?null:'Enter 10–15 digits without spaces or hyphens, for example +919876543210.'},
} satisfies Record<string,FieldFormat>

/** Null while the field is empty or valid; otherwise what to fix. */
export function formatWarning(format:FieldFormat,value:string):string|null{
  return value?format.check(value):null
}
