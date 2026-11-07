import {Plus,X} from 'lucide-react'
import AddressSearchField from './AddressSearchField'
import {MAX_STOPS,STOP_ACTIVITIES,readStops,writeStops,type Stop} from '../lib/stops'

/** Optional stops between pickup and drop; stored as one text field so drafts keep working. */
export default function StopsEditor({value,onChange}:{value:string;onChange:(value:string)=>void}){
  const stops=readStops(value)
  const update=(next:Stop[])=>onChange(writeStops(next))
  const change=(index:number,patch:Partial<Stop>)=>update(stops.map((stop,position)=>position===index?{...stop,...patch}:stop))
  return <section className="stops-editor" aria-labelledby="stops-heading">
    <div className="stops-head"><h3 id="stops-heading">Stops on the way <small>optional</small></h3><p>Add places the truck must stop between pickup and drop. Truck owners see how many stops there are and include them in their quote; exact addresses stay private.</p></div>
    {stops.length>0&&<ol className="stops-list">{stops.map((stop,index)=><li key={index} className="stop-row">
      <span className="stop-number" aria-hidden="true">{index+1}</span>
      <div className="stop-fields">
        <AddressSearchField id={`stop-${index+1}-address`} label={`Stop ${index+1} address`} value={stop.address} onType={text=>change(index,{address:text})} onPick={place=>change(index,{address:place.address})} required minLength={3} maxLength={500} placeholder="Start typing, then pick from the list"/>
        <label>What happens here<select value={stop.activity} onChange={event=>change(index,{activity:event.target.value as Stop['activity']})}>{STOP_ACTIVITIES.map(([key,label])=><option key={key} value={key}>{label}</option>)}</select></label>
        <label>Note for this stop — optional<input value={stop.note} maxLength={1000} onChange={event=>change(index,{note:event.target.value})} placeholder="For example: 4 cartons, use gate 2"/></label>
      </div>
      <button type="button" className="secondary stop-remove" aria-label={`Remove stop ${index+1}`} onClick={()=>update(stops.filter((_,position)=>position!==index))}><X/></button>
    </li>)}</ol>}
    {stops.length<MAX_STOPS?<button type="button" className="secondary stop-add" onClick={()=>update([...stops,{address:'',activity:'drop',note:''}])}><Plus/> {stops.length?'Add another stop':'Add a stop'}</button>:<p>You have added the maximum of {MAX_STOPS} stops.</p>}
  </section>
}
