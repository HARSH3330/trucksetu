import {beforeEach,expect,it,vi} from 'vitest'
import {apiFetch,restoreSession,saveSession,logoutSession} from './api'

const storage=()=>{const values=new Map<string,string>();return {getItem:(key:string)=>values.get(key)||null,setItem:(key:string,value:string)=>values.set(key,value),removeItem:(key:string)=>values.delete(key),clear:()=>values.clear()}}
beforeEach(()=>{vi.stubGlobal('sessionStorage',storage());vi.stubGlobal('localStorage',storage());vi.stubGlobal('window',{dispatchEvent:vi.fn()})})

it('restores current role from cookie refresh without a JS refresh token',async()=>{
  const fetch=vi.fn().mockResolvedValueOnce(new Response(JSON.stringify({access_token:'fictional-access',user:{id:'a',roles:['admin']}}))).mockResolvedValueOnce(new Response(JSON.stringify({id:'a',roles:['admin']})))
  vi.stubGlobal('fetch',fetch)
  await expect(restoreSession()).resolves.toMatchObject({id:'a',roles:['admin']})
  expect(fetch.mock.calls[0][0]).toMatch(/\/auth\/session\/refresh$/)
  expect(fetch.mock.calls[0][1].credentials).toBe('include')
  expect(new Headers(fetch.mock.calls[0][1].headers).get('X-TransivoX-CSRF')).toBe('1')
  expect(sessionStorage.getItem('transivox_refresh_token')).toBeNull()
  expect(localStorage.getItem('transivox_refresh_token')).toBeNull()
})

it('logs out cookie-only sessions even with no browser refresh credential',async()=>{
  saveSession({access_token:'fictional-access'})
  const fetch=vi.fn().mockResolvedValue(new Response(null,{status:204}));vi.stubGlobal('fetch',fetch)
  await logoutSession()
  expect(fetch.mock.calls[0][0]).toMatch(/\/auth\/session\/logout$/)
  expect(sessionStorage.getItem('transivox_access_token')).toBeNull()
})

it('rejects a previous account response when the account changes during JSON parsing',async()=>{
  saveSession({access_token:'fictional-account-a'})
  let release!:(value:unknown)=>void
  let parsing!:()=>void
  const started=new Promise<void>(resolve=>{parsing=resolve})
  vi.stubGlobal('fetch',vi.fn().mockResolvedValue({ok:true,status:200,json:()=>{parsing();return new Promise(resolve=>{release=resolve})}}))
  const request=apiFetch('/auth/me')
  const rejected=expect(request).rejects.toMatchObject({status:401})
  await started
  saveSession({access_token:'fictional-account-b'})
  release({id:'account-a',roles:['admin']})
  await rejected
})

it('does not silently restore a cookie after an explicit offline logout and page reload',async()=>{
  saveSession({access_token:'fictional-account-a'})
  const fetch=vi.fn().mockRejectedValue(new Error('Offline'));vi.stubGlobal('fetch',fetch)
  await expect(logoutSession()).rejects.toMatchObject({status:0})
  fetch.mockReset().mockResolvedValue(new Response(JSON.stringify({access_token:'fictional-account-a',id:'account-a',roles:['admin']})))
  await expect(restoreSession()).resolves.toBeNull()
  expect(fetch).not.toHaveBeenCalled()
  fetch.mockResolvedValue(new Response(JSON.stringify({detail:'Sign in required'}),{status:401}))
  await expect(apiFetch('/bookings')).rejects.toMatchObject({status:401})
  expect(fetch).toHaveBeenCalledTimes(1)
  saveSession({access_token:'fictional-account-b'})
  fetch.mockResolvedValue(new Response(JSON.stringify({id:'account-b',roles:['customer']})))
  await expect(restoreSession()).resolves.toMatchObject({id:'account-b'})
})
