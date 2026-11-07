export type AccountEmailLink={mode:'reset'|'verify';email:string;token:string;code:string}
export function parseAccountEmailLink(hash:string):AccountEmailLink|null{
  const [route,query]=hash.replace(/^#\/?/,'').split('?')
  if(route!=='account-reset'&&route!=='account-verify')return null
  const params=new URLSearchParams(query),email=params.get('email')??''
  if(email.length>254||!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email))return null
  const token=params.get('token')??'',code=params.get('code')??''
  if(route==='account-reset'&&/^[A-Za-z0-9_-]{32,128}$/.test(token))return{mode:'reset',email,token,code:''}
  if(route==='account-verify'&&/^\d{6}$/.test(code))return{mode:'verify',email,token:'',code}
  return null
}
