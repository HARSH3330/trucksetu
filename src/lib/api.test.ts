import {beforeEach, describe, expect, it, vi} from 'vitest'
import {apiErrorMessage, apiFetch, clearSession, saveSession, logoutSession} from './api'

class MemoryStorage {
  private values = new Map<string,string>()
  getItem(key:string){return this.values.get(key)??null}
  setItem(key:string,value:string){this.values.set(key,value)}
  removeItem(key:string){this.values.delete(key)}
}

beforeEach(()=>{
  vi.stubGlobal('sessionStorage',new MemoryStorage())
  vi.stubGlobal('localStorage',new MemoryStorage())
  vi.restoreAllMocks()
})

describe('API error messages',()=>{
  it('turns FastAPI validation details into safe field-specific guidance',()=>{
    expect(apiErrorMessage({detail:[
      {type:'value_error',loc:['body','password'],msg:'Value error, Password must include uppercase, lowercase, and numeric characters',input:'secret-value'},
      {type:'value_error',loc:['body','email'],msg:'value is not a valid email address: An email address must have an @-sign.',input:'invalid-address'},
    ]},'Unable to continue')).toBe(
      'Password: Password must include uppercase, lowercase, and numeric characters. Email address: Enter a valid email address.',
    )
  })

  it('preserves a normal API error and falls back for malformed responses',()=>{
    expect(apiErrorMessage({detail:'This email is already registered'},'Unable to continue')).toBe('This email is already registered')
    expect(apiErrorMessage({detail:[]},'Unable to continue')).toBe('Unable to continue')
  })
})

describe('authenticated API client',()=>{
  it('revokes the refresh credential and clears client storage on logout',async()=>{
    saveSession({access_token:'fictional-access',refresh_token:'fictional-refresh'})
    const fetchMock=vi.fn().mockResolvedValue(new Response(null,{status:204}))
    vi.stubGlobal('fetch',fetchMock)
    await logoutSession()
    expect(fetchMock.mock.calls[0][0]).toMatch(/\/auth\/logout$/)
    expect(JSON.parse(fetchMock.mock.calls[0][1].body)).toEqual({refresh_token:'fictional-refresh'})
    expect(sessionStorage.getItem('transivox_access_token')).toBeNull()
    expect(sessionStorage.getItem('transivox_refresh_token')).toBeNull()
  })

  it('clears local credentials even when server revocation is unavailable',async()=>{
    saveSession({access_token:'fictional-access',refresh_token:'fictional-refresh'})
    vi.stubGlobal('fetch',vi.fn().mockRejectedValue(new TypeError('offline')))
    await expect(logoutSession()).rejects.toMatchObject({status:0})
    expect(sessionStorage.getItem('transivox_refresh_token')).toBeNull()
  })

  it('does not restore credentials when an in-flight refresh completes after logout',async()=>{
    saveSession({access_token:'old',refresh_token:'old-refresh'})
    let resolveRefresh!:(response:Response)=>void
    let started!:(value:void)=>void
    const start=new Promise<void>(resolve=>{started=resolve})
    vi.stubGlobal('fetch',vi.fn((url:string)=>{
      if(url.endsWith('/auth/refresh')){started();return new Promise<Response>(resolve=>{resolveRefresh=resolve})}
      if(url.endsWith('/auth/logout'))return Promise.resolve(new Response(null,{status:204}))
      return Promise.resolve(new Response('{}',{status:401}))
    }))
    const pending=apiFetch('/auth/me').catch(error=>error)
    await start
    // Logout clears UI credentials immediately, but its server mutation now
    // waits for the cross-tab session lock held by this in-flight refresh.
    const signingOut=logoutSession()
    resolveRefresh(new Response(JSON.stringify({access_token:'rotated',refresh_token:'rotated-refresh'})))
    await signingOut
    expect(await pending).toMatchObject({status:401})
    expect(sessionStorage.getItem('transivox_access_token')).toBeNull()
  })

  it('does not clear a newer login when an older refresh finishes',async()=>{
    saveSession({access_token:'old',refresh_token:'old-refresh'})
    let resolveRefresh!:(response:Response)=>void
    let started!:(value:void)=>void
    const start=new Promise<void>(resolve=>{started=resolve})
    vi.stubGlobal('fetch',vi.fn((url:string)=>{
      if(url.endsWith('/auth/refresh')){started();return new Promise<Response>(resolve=>{resolveRefresh=resolve})}
      return Promise.resolve(new Response('{}',{status:401}))
    }))
    const pending=apiFetch('/auth/me').catch(error=>error)
    await start
    saveSession({access_token:'new-login',refresh_token:'new-login-refresh'})
    resolveRefresh(new Response('{}',{status:401}))
    await pending
    expect(sessionStorage.getItem('transivox_access_token')).toBe('new-login')
  })
  it('stores tokens only for the browser session',()=>{
    saveSession({access_token:'access',refresh_token:'refresh'})
    expect(sessionStorage.getItem('transivox_refresh_token')).toBe('refresh')
    expect(localStorage.getItem('transivox_refresh_token')).toBeNull()
    clearSession()
    expect(sessionStorage.getItem('transivox_access_token')).toBeNull()
  })

  it('rotates an expired access token and retries once',async()=>{
    saveSession({access_token:'old',refresh_token:'refresh'})
    const fetchMock=vi.fn()
      .mockResolvedValueOnce(new Response('{}',{status:401,headers:{'Content-Type':'application/json'}}))
      .mockResolvedValueOnce(new Response(JSON.stringify({access_token:'new',refresh_token:'new-refresh'}),{status:200,headers:{'Content-Type':'application/json'}}))
      .mockResolvedValueOnce(new Response(JSON.stringify({id:'me'}),{status:200,headers:{'Content-Type':'application/json'}}))
    vi.stubGlobal('fetch',fetchMock)
    await expect(apiFetch<{id:string}>('/auth/me')).resolves.toEqual({id:'me'})
    expect(fetchMock).toHaveBeenCalledTimes(3)
    expect(sessionStorage.getItem('transivox_access_token')).toBe('new')
  })

  it('retries one temporary GET failure',async()=>{
    const fetchMock=vi.fn()
      .mockRejectedValueOnce(new TypeError('network unavailable'))
      .mockResolvedValueOnce(new Response(JSON.stringify({status:'ready'}),{status:200,headers:{'Content-Type':'application/json'}}))
    vi.stubGlobal('fetch',fetchMock)
    await expect(apiFetch<{status:string}>('/health')).resolves.toEqual({status:'ready'})
    expect(fetchMock).toHaveBeenCalledTimes(2)
  })

  it('does not retry a failed write that may have reached the server',async()=>{
    const fetchMock=vi.fn().mockRejectedValue(new TypeError('network unavailable'))
    vi.stubGlobal('fetch',fetchMock)
    await expect(apiFetch('/requests',{method:'POST',body:'{}'})).rejects.toMatchObject({
      status:0,message:'Unable to reach TransivoX. Check your connection and try again.',
    })
    expect(fetchMock).toHaveBeenCalledTimes(1)
  })
})
