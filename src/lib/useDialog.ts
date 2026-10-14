import {useEffect,useRef} from 'react'

/** Keyboard containment and focus restoration for the existing modal layout. */
export function useDialog(close:()=>void){
  const ref=useRef<HTMLDivElement>(null)
  const closeRef=useRef(close)
  closeRef.current=close
  useEffect(()=>{
    const element=ref.current
    if(!element)return
    const previous=document.activeElement as HTMLElement|null
    const overflow=document.body.style.overflow
    document.body.style.overflow='hidden'
    const controls=()=>Array.from(element.querySelectorAll<HTMLElement>('button:not(:disabled),input:not(:disabled),select:not(:disabled),textarea:not(:disabled),a[href],[tabindex="0"]')).filter(item=>item.getClientRects().length>0)
    ;(controls()[0]||element).focus()
    function keyboard(event:KeyboardEvent){
      if(event.key==='Escape'){event.preventDefault();closeRef.current();return}
      if(event.key!=='Tab')return
      const items=controls(),first=items[0],last=items[items.length-1]
      if(!first){event.preventDefault();element?.focus();return}
      if(event.shiftKey&&(document.activeElement===first||!element?.contains(document.activeElement))){event.preventDefault();last.focus()}
      else if(!event.shiftKey&&(document.activeElement===last||!element?.contains(document.activeElement))){event.preventDefault();first.focus()}
    }
    element.addEventListener('keydown',keyboard)
    return()=>{element.removeEventListener('keydown',keyboard);document.body.style.overflow=overflow;previous?.focus()}
  },[])
  return ref
}
