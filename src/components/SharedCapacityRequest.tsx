import {useState} from 'react'
import {apiFetch,type AvailableRoute} from '../lib/api'

export default function SharedCapacityRequest({route}:{route:AvailableRoute}){
  const [values,setValues]=useState<Record<string,string>>({}),[busy,setBusy]=useState(false),[message,setMessage]=useState('')
  const fields=[['category','Cargo category','text'],['description','Cargo description','text'],['weight','Weight (tonnes)','number'],['length','Total cargo length (m)','number'],['width','Total cargo width (m)','number'],['height','Total cargo height (m)','number'],['start','Earliest pickup','datetime-local'],['end','Latest pickup','datetime-local'],['deadline','Delivery deadline','datetime-local'],['added','Maximum added time (minutes)','number']] as const
  async function submit(event:React.FormEvent){
    event.preventDefault();if(busy)return;setBusy(true);setMessage('')
    try{
      const start=new Date(values.start)
      const date=new Intl.DateTimeFormat('en-CA',{timeZone:'Asia/Kolkata',year:'numeric',month:'2-digit',day:'2-digit'}).format(start)
      const created=await apiFetch<{public_id:string}>('/requests',{method:'POST',body:JSON.stringify({available_route_id:route.id,vehicle_category_id:route.vehicle_category_id,booking_mode:'SHARED_CAPACITY',schedule_mode:'SCHEDULED',pickup_date:date,earliest_pickup_at:start.toISOString(),latest_pickup_at:new Date(values.end).toISOString(),delivery_deadline_at:new Date(values.deadline).toISOString(),maximum_added_time_minutes:Number(values.added),pickup_address:route.origin,pickup_city:route.origin,destination_address:route.destination,destination_city:route.destination,vehicle_count:1,publish:true,cargo:{category:values.category,description:values.description,weight_tonnes:values.weight,length_m:values.length,width_m:values.width,height_m:values.height}})})
      setMessage(`Request ${created.public_id} sent. This does not reserve capacity. Review the provider quotation in Quotations; route suitability must also be reviewed before booking.`)
    }catch(error){setMessage(error instanceof Error?error.message:'Capacity request unavailable')}
    finally{setBusy(false)}
  }
  return <details><summary>Request capacity on this route</summary><form className="fields" onSubmit={submit}><p>No guaranteed space or final price until a current provider quotation is explicitly accepted and the server confirms the booking.</p>{fields.map(([key,label,type])=><label key={key}>{label}<input required disabled={busy} type={type} min={type==='number'?(key==='added'?'0':'0.001'):undefined} step={type==='number'?(key==='added'?'1':'0.001'):undefined} maxLength={type==='text'?2000:undefined} value={values[key]||''} onChange={event=>setValues({...values,[key]:event.target.value})}/></label>)}<button disabled={busy}>{busy?'Requesting…':'Request provider quotation'}</button>{message&&<p role="status">{message}</p>}</form></details>
}
