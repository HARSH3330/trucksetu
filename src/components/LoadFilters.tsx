import {useState} from 'react'
import {useDialog} from '../lib/useDialog'

export type LoadFilter={cargo:string;date:string;vehicles:string}
export const EMPTY_LOAD_FILTER:LoadFilter={cargo:'',date:'',vehicles:''}
export default function LoadFilters({value,categories,onApply,onClose}:{value:LoadFilter;categories:string[];onApply:(value:LoadFilter)=>void;onClose:()=>void}){
  const dialog=useDialog(onClose)
  const [draft,setDraft]=useState(value)
  return <div className="overlay filters-overlay"><div ref={dialog} className="modal filters-dialog" role="dialog" aria-modal="true" aria-labelledby="load-filter-title" tabIndex={-1}><button className="modal-close" onClick={onClose} aria-label="Close filters">×</button><h2 id="load-filter-title">Filter loads</h2><p>Filter the currently loaded published requirements.</p><form className="auth-form" onSubmit={event=>{event.preventDefault();onApply(draft);onClose()}}><label>Cargo type<select aria-label="Cargo type" value={draft.cargo} onChange={event=>setDraft({...draft,cargo:event.target.value})}><option value="">All cargo</option>{categories.map(cargo=><option key={cargo}>{cargo}</option>)}</select></label><label>Pickup date<input type="date" value={draft.date} onChange={event=>setDraft({...draft,date:event.target.value})}/></label><label>Vehicles required<select aria-label="Vehicles required" value={draft.vehicles} onChange={event=>setDraft({...draft,vehicles:event.target.value})}><option value="">Any count</option><option value="1">One vehicle</option><option value="multiple">Multiple vehicles</option></select></label><button type="button" onClick={()=>setDraft(EMPTY_LOAD_FILTER)}>Reset filters</button><button className="auth-submit">Apply filters</button></form></div></div>
}
