import {useEffect,useState} from 'react'

/** Short, plain countdown such as "3 h 20 min left". */
export function timeLeft(until:string,now:Date=new Date()):string{
  const end=new Date(until).getTime()
  if(!Number.isFinite(end))return ''
  const minutes=Math.floor((end-now.getTime())/60000)
  if(end<=now.getTime())return 'expired'
  if(minutes<1)return 'less than a minute left'
  const days=Math.floor(minutes/1440),hours=Math.floor(minutes%1440/60),rest=minutes%60
  if(days)return `${days} day${days>1?'s':''}${hours?` ${hours} h`:''} left`
  return hours?`${hours} h${rest?` ${rest} min`:''} left`:`${rest} min left`
}

/** Re-renders once a minute so countdowns stay current. */
export function useMinuteClock():Date{
  const [now,setNow]=useState(()=>new Date())
  useEffect(()=>{const timer=window.setInterval(()=>setNow(new Date()),60000);return()=>window.clearInterval(timer)},[])
  return now
}
