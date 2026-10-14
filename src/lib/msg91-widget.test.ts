import {afterEach,expect,it,vi} from 'vitest'

afterEach(()=>{vi.unstubAllGlobals();vi.resetModules()})

it('falls back to the second script and shares one pending loader',async()=>{
  const widgetWindow:{initSendOTP?:()=>void}={}
  const sources:string[]=[]
  vi.stubGlobal('window',widgetWindow)
  vi.stubGlobal('document',{createElement:()=>({remove:()=>{}}),head:{appendChild:(script:{src:string;onerror:()=>void;onload:()=>void})=>{sources.push(script.src);queueMicrotask(()=>{if(sources.length===1)script.onerror();else{widgetWindow.initSendOTP=()=>{};script.onload()}})}}})
  const {loadMsg91Widget}=await import('./msg91-widget')
  const [a,b]=await Promise.all([loadMsg91Widget(),loadMsg91Widget()])
  expect(a).toBe(b)
  expect(sources).toEqual(['https://verify.msg91.com/otp-provider.js','https://verify.phone91.com/otp-provider.js'])
})

it('rejects if scripts load without a usable initializer',async()=>{
  vi.stubGlobal('window',{})
  vi.stubGlobal('document',{createElement:()=>({remove:()=>{}}),head:{appendChild:(script:{onload:()=>void})=>queueMicrotask(()=>script.onload())}})
  const {loadMsg91Widget}=await import('./msg91-widget')
  await expect(loadMsg91Widget()).rejects.toThrow('Phone verification widget could not be loaded')
})

it('extracts only bounded token strings, never marks callback data verified',async()=>{
  const {widgetToken}=await import('./msg91-widget')
  expect(widgetToken({type:'success',message:'fictional-widget-token-not-for-real-use'})).toBe('fictional-widget-token-not-for-real-use')
  expect(widgetToken({type:'error',message:'fictional-widget-token-not-for-real-use'})).toBeNull()
  expect(widgetToken({type:'success',message:{verified:true}})).toBeNull()
  expect(widgetToken('short')).toBeNull()
  expect(widgetToken('x'.repeat(4097))).toBeNull()
})

it('supplies a country-coded identifier for legacy ten-digit Indian contacts',async()=>{
  const {widgetIdentifier}=await import('./msg91-widget')
  expect(widgetIdentifier('9999999999')).toBe('919999999999')
  expect(widgetIdentifier('+919999999999')).toBe('919999999999')
})
