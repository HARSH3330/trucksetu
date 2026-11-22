import {useEffect,useRef,useState} from 'react'
import {newSearchSession,nextOption,resolveSuggestion,shouldSearch,suggestPlaces,type PlaceValue,type Suggestion} from '../lib/places'

type Props={
  id:string;label:string;value:string
  /** Manual typing; the text is always kept even when Google is unavailable. */
  onType:(text:string)=>void
  /** Called with the chosen Google place. */
  onPick:(place:PlaceValue)=>void
  /** Returns the form state a late result must not overwrite once it has changed. */
  snapshot?:()=>string
  cities?:boolean;required?:boolean;minLength?:number;maxLength?:number;placeholder?:string
}

const UNAVAILABLE='Address suggestions are unavailable right now. Type the full address yourself.'

export default function AddressSearchField({id,label,value,onType,onPick,snapshot,cities=false,required,minLength,maxLength,placeholder}:Props){
  const [options,setOptions]=useState<Suggestion[]>([])
  const [open,setOpen]=useState(false)
  const [active,setActive]=useState(-1)
  const [status,setStatus]=useState('')
  const typed=useRef(false),sequence=useRef(0),session=useRef<unknown>(null)
  const listId=id+'-suggestions'

  useEffect(()=>{
    if(!typed.current)return
    typed.current=false
    const run=++sequence.current
    if(!shouldSearch(value)){setOptions([]);setOpen(false);return}
    const timer=window.setTimeout(async()=>{
      try{
        session.current??=await newSearchSession()
        const found=await suggestPlaces(value,session.current,cities)
        if(run!==sequence.current)return
        setOptions(found);setActive(-1);setOpen(true);setStatus(found.length?'':'No matching places. Check the spelling or type the full address.')
      }catch{if(run===sequence.current){setOptions([]);setOpen(false);setStatus(UNAVAILABLE)}}
    },300)
    return()=>window.clearTimeout(timer)
  },[value,cities])

  async function pick(option:Suggestion){
    const run=++sequence.current,before=snapshot?.()
    setOpen(false);setStatus('Getting the selected place…')
    try{
      const place=await resolveSuggestion(option)
      if(run!==sequence.current||(snapshot&&snapshot()!==before))return
      session.current=null
      setStatus('');onPick(place)
    }catch{if(run===sequence.current)setStatus(UNAVAILABLE)}
  }

  function keyboard(event:React.KeyboardEvent<HTMLInputElement>){
    if(event.key==='Escape'&&open){event.preventDefault();setOpen(false);return}
    if(!open||!options.length)return
    if(['ArrowDown','ArrowUp','Home','End'].includes(event.key)){event.preventDefault();setActive(current=>nextOption(current,options.length,event.key))}
    else if(event.key==='Enter'&&active>=0){event.preventDefault();void pick(options[active])}
  }

  return <div className="address-search">
    <label htmlFor={id}>{label}</label>
    <input id={id} role="combobox" aria-autocomplete="list" aria-expanded={open} aria-controls={listId} aria-activedescendant={open&&active>=0?`${listId}-${active}`:undefined} autoComplete="off"
      required={required} minLength={minLength} maxLength={maxLength} placeholder={placeholder} value={value}
      onChange={event=>{typed.current=true;onType(event.target.value)}} onKeyDown={keyboard} onBlur={()=>window.setTimeout(()=>setOpen(false),150)}/>
    {open&&options.length>0&&<ul role="listbox" id={listId} className="address-suggestions" aria-label={label+' suggestions'}>
      {options.map((option,index)=><li role="option" id={`${listId}-${index}`} key={option.id} aria-selected={index===active} className={index===active?'active':undefined}
        onMouseDown={event=>event.preventDefault()} onClick={()=>void pick(option)}><b>{option.main}</b>{option.secondary&&<small>{option.secondary}</small>}</li>)}
      <li className="address-attribution" aria-hidden="true">Powered by Google</li>
    </ul>}
    {status&&<small className="address-status" role="status">{status}</small>}
  </div>
}
