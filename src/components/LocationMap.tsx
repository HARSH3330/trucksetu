import {useEffect,useRef,useState} from 'react'
import {loadGoogleMaps,mapFailure,type MapInstance,type MapLibraries,type MarkerInstance} from '../lib/google-maps'
import type {Endpoint,MapPoint} from '../lib/demand-location'

type Props={
  points:Record<Endpoint,MapPoint|null>
  /** Dragging a pin reports its new position; omit for a read-only map. */
  onMove?:(end:Endpoint,point:MapPoint)=>void
  /** Tapping the map reports a position for the caller's selected pin. */
  onTap?:(point:MapPoint)=>void
}

const TITLES:Record<Endpoint,string>={pickup:'Pickup pin',destination:'Drop pin'}

/** Appears below the address fields only once a place has been chosen. */
export default function LocationMap({points,onMove,onTap}:Props){
  const visible=Boolean(points.pickup||points.destination)
  const canvas=useRef<HTMLDivElement>(null),map=useRef<MapInstance|null>(null),libs=useRef<MapLibraries|null>(null)
  const markers=useRef<Partial<Record<Endpoint,MarkerInstance>>>({})
  const latest=useRef({onMove,onTap});latest.current={onMove,onTap}
  const [ready,setReady]=useState(false),[status,setStatus]=useState(''),[attempt,setAttempt]=useState(0)

  useEffect(()=>{
    if(!visible||!canvas.current)return
    let alive=true,listener:{remove:()=>void}|null=null
    const fail=()=>{if(alive){setReady(false);setStatus(mapFailure)}}
    window.addEventListener('transivox-maps-error',fail)
    setStatus('Loading map…')
    void loadGoogleMaps().then(sdk=>{
      if(!alive||!canvas.current)return
      libs.current=sdk
      map.current=new sdk.maps.Map(canvas.current,{center:{lat:22.5,lng:79},zoom:5,mapId:import.meta.env.VITE_GOOGLE_MAPS_MAP_ID||'DEMO_MAP_ID',gestureHandling:'cooperative',streetViewControl:false,mapTypeControl:false})
      listener=map.current.addListener('click',event=>{if(event.latLng)latest.current.onTap?.({lat:event.latLng.lat(),lng:event.latLng.lng()})})
      setReady(true);setStatus('')
    }).catch(fail)
    return()=>{alive=false;window.removeEventListener('transivox-maps-error',fail);listener?.remove();Object.values(markers.current).forEach(marker=>{if(marker)marker.map=null});markers.current={};map.current=null;libs.current=null;setReady(false);canvas.current?.replaceChildren()}
  },[visible,attempt])

  useEffect(()=>{
    if(!ready||!map.current||!libs.current)return
    let focus:MapPoint|null=null
    for(const end of ['pickup','destination'] as const){
      const point=points[end],old=markers.current[end]
      if(!point){if(old)old.map=null;delete markers.current[end];continue}
      focus=point
      if(old){old.position=point;continue}
      const marker=new libs.current.marker.AdvancedMarkerElement({map:map.current,position:point,gmpDraggable:Boolean(onMove),title:TITLES[end]})
      marker.addEventListener('gmp-dragend',()=>{const p=marker.position;if(p)latest.current.onMove?.(end,{lat:typeof p.lat==='function'?p.lat():p.lat,lng:typeof p.lng==='function'?p.lng():p.lng})})
      markers.current[end]=marker
    }
    if(focus){map.current.setCenter(focus);map.current.setZoom(points.pickup&&points.destination?11:15)}
  },[points.pickup?.lat,points.pickup?.lng,points.destination?.lat,points.destination?.lng,ready,onMove])

  if(!visible)return null
  return <div className="location-map">
    {status&&<p role="status">{status}</p>}
    {status===mapFailure&&<button type="button" className="secondary" onClick={()=>setAttempt(value=>value+1)}>Retry map</button>}
    <div ref={canvas} className="location-map-canvas" aria-label="Map of the chosen locations"/>
  </div>
}
