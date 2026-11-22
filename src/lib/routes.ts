import {useCallback,useEffect,useState} from 'react'

const views=['home','ship','requirements','loads','quotes','capacity','bookings','trust','support','terms','privacy','refund','communications','dashboard','admin','kyc','fleet','payments','invoices','trips','vehicle-review','pricing'] as const
export type View=typeof views[number]
export function viewFromHash(hash:string):View{
  const value=hash.replace(/^#\/?/,'').split('?')[0]
  return views.includes(value as View)?value as View:'home'
}
export function useHashView():[View,(view:View)=>void]{
  const [view,setView]=useState<View>(()=>viewFromHash(window.location.hash))
  useEffect(()=>{
    const sync=()=>setView(viewFromHash(window.location.hash))
    window.addEventListener('hashchange',sync)
    window.addEventListener('popstate',sync)
    return()=>{window.removeEventListener('hashchange',sync);window.removeEventListener('popstate',sync)}
  },[])
  const navigate=useCallback((next:View)=>{
    if(window.location.hash!==`#${next}`)window.history.pushState(null,'',`#${next}`)
    setView(next)
    window.scrollTo({top:0,behavior:'instant'})
  },[])
  return [view,navigate]
}
