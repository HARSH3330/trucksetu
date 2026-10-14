export type WidgetConfiguration={widgetId:string;tokenAuth:string;identifier:string;exposeMethods:false;success:(data:unknown)=>void;failure:(error:unknown)=>void}
type Initializer=(configuration:WidgetConfiguration)=>void
declare global {interface Window {initSendOTP?:Initializer}}

let pending:Promise<Initializer>|null=null
const sources=['https://verify.msg91.com/otp-provider.js','https://verify.phone91.com/otp-provider.js']

export function loadMsg91Widget():Promise<Initializer>{
  if(typeof window.initSendOTP==='function')return Promise.resolve(window.initSendOTP)
  if(pending)return pending
  pending=new Promise<Initializer>((resolve,reject)=>{
    function attempt(index:number){
      if(index>=sources.length){reject(new Error('Phone verification widget could not be loaded'));return}
      const script=document.createElement('script');script.src=sources[index];script.async=true
      const timeout=setTimeout(fallback,10_000)
      let finished=false
      function finish(){if(finished)return false;finished=true;clearTimeout(timeout);script.onload=null;script.onerror=null;return true}
      function fallback(){if(!finish())return;script.remove();attempt(index+1)}
      script.onerror=fallback
      script.onload=()=>{if(typeof window.initSendOTP!=='function'){fallback();return}if(finish())resolve(window.initSendOTP)}
      document.head.appendChild(script)
    }
    attempt(0)
  }).catch(error=>{pending=null;throw error})
  return pending
}

export function widgetToken(data:unknown):string|null{
  let candidate:unknown=data
  if(data&&typeof data==='object'){
    const result=data as Record<string,unknown>
    if(result.type!=='success')return null
    candidate=result.token??result['access-token']??result.message
  }
  return typeof candidate==='string'&&candidate.length>=20&&candidate.length<=4096?candidate:null
}

export function widgetIdentifier(mobile:string):string{
  const digits=mobile.replace(/^\+/,'')
  return !mobile.startsWith('+')&&digits.length===10?'91'+digits:digits
}
