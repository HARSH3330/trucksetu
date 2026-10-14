import React,{useEffect,useState} from 'react'
import {publicFetch,type MarketplaceRequest} from '../lib/api'

export default function PublicLoadsPreview({renderLoad}:{renderLoad:(item:MarketplaceRequest,index:number)=>React.ReactNode}){
  const [items,setItems]=useState<MarketplaceRequest[]>([])
  const [state,setState]=useState<'loading'|'ready'|'error'>('loading')
  const [retry,setRetry]=useState(0)
  useEffect(()=>{
    let cancelled=false
    setState('loading')
    publicFetch<MarketplaceRequest[]>('/requests').then(rows=>{if(!cancelled){setItems(rows.slice(0,3));setState('ready')}}).catch(()=>{if(!cancelled)setState('error')})
    return()=>{cancelled=true}
  },[retry])
  if(state==='loading')return <div className="empty-state" role="status">Loading current loads…</div>
  if(state==='error')return <div className="empty-state"><b>Current loads are unavailable.</b><p>Please retry or post your own requirement.</p><button onClick={()=>setRetry(value=>value+1)}>Retry current loads</button></div>
  if(!items.length)return <div className="empty-state">No published loads currently available.</div>
  return <div className="cards">{items.map(renderLoad)}</div>
}
