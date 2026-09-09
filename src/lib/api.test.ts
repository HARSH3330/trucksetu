import {beforeEach, describe, expect, it, vi} from 'vitest'
import {apiFetch, clearSession, saveSession} from './api'

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

describe('authenticated API client',()=>{
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
})
