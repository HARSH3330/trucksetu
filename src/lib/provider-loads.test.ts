import {describe,expect,it} from 'vitest'
import {loadProviderWorkspace} from './provider-loads'

const demand={id:'d1'}
function fake(responses:Record<string,unknown|Error>){
  const calls:string[]=[]
  const fetch=async<T>(path:string):Promise<T>=>{calls.push(path);const value=responses[path];if(value instanceof Error)throw value;if(value===undefined)throw new Error('unexpected '+path);return value as T}
  return {fetch,calls}
}

describe('provider workspace loading',()=>{
  it('shows open requirements to a truck owner who has no provider profile yet',async()=>{
    const {fetch}=fake({'/demands?pickup=':[demand],'/providers/me':new Error('Complete your provider verification profile before quoting'),'/demand-bids/mine':new Error('forbidden'),'/demand-selections/mine':new Error('forbidden'),'/carrier-vehicles':[]})
    const result=await loadProviderWorkspace(fetch,new URLSearchParams({pickup:''}))
    expect(result.demands).toEqual([demand])
    expect(result.profile).toBeNull()
    expect(result.canBid).toBe(false)
    expect(result.bids).toEqual([]);expect(result.selections).toEqual([]);expect(result.drivers).toEqual([])
    expect(result.unavailable).toEqual([])
  })
  it('lets only an active verified provider bid',async()=>{
    const verified={id:'p1',kyc_status:'verified',active:true}
    const {fetch,calls}=fake({'/demands?':[demand],'/providers/me':verified,'/demand-bids/mine':[],'/demand-selections/mine':[],'/carrier-vehicles':[{id:'v1'}],'/providers/p1/drivers':[{id:'r1'}]})
    const result=await loadProviderWorkspace(fetch,new URLSearchParams())
    expect(result.canBid).toBe(true)
    expect(result.vehicles).toEqual([{id:'v1'}]);expect(result.drivers).toEqual([{id:'r1'}])
    expect(calls).toContain('/providers/p1/drivers')
    const pending=await loadProviderWorkspace(fake({'/demands?':[],'/providers/me':{...verified,kyc_status:'under_review'},'/demand-bids/mine':new Error('forbidden'),'/demand-selections/mine':new Error('forbidden'),'/carrier-vehicles':[],'/providers/p1/drivers':[]}).fetch,new URLSearchParams())
    expect(pending.canBid).toBe(false)
    expect(pending.unavailable).toEqual([])
  })
  it('names the sections a verified provider could not load instead of hiding them silently',async()=>{
    const {fetch}=fake({'/demands?':[],'/providers/me':{id:'p1',kyc_status:'verified',active:true},'/demand-bids/mine':new Error('down'),'/demand-selections/mine':[],'/carrier-vehicles':new Error('down'),'/providers/p1/drivers':[]})
    const result=await loadProviderWorkspace(fetch,new URLSearchParams())
    expect(result.unavailable).toEqual(['your bids','your trucks'])
  })
  it('still fails when the requirements themselves cannot be loaded',async()=>{
    const {fetch}=fake({'/demands?':new Error('Workspace down')})
    await expect(loadProviderWorkspace(fetch,new URLSearchParams())).rejects.toThrow('Workspace down')
  })
})
