import type {MapPoint} from './demand-location'
export type LatLng={lat:()=>number;lng:()=>number}
export type Place={formattedAddress?:string;location?:LatLng;addressComponents?:{longText:string;types:string[]}[];fetchFields:(o:{fields:string[]})=>Promise<unknown>}
export type SelectPlaceEvent=Event&{placePrediction:{toPlace:()=>Place}}
export type MapInstance={setCenter:(p:MapPoint)=>void;setZoom:(z:number)=>void;addListener:(n:string,cb:(e:{latLng?:LatLng})=>void)=>{remove:()=>void}}
export type MarkerInstance=HTMLElement&{position:MapPoint|LatLng|null;map:MapInstance|null}
export type MapLibraries={maps:{Map:new(el:HTMLElement,o:object)=>MapInstance};places:{PlaceAutocompleteElement:new(o?:object)=>HTMLElement};marker:{AdvancedMarkerElement:new(o:object)=>MarkerInstance}}
type MapsGlobal={maps:{importLibrary:(name:string)=>Promise<unknown>}}
declare global{interface Window{google?:MapsGlobal;gm_authFailure?:()=>void;transivoxMapsReady?:()=>void}}
let loading:Promise<MapLibraries>|null=null
export const mapFailure='Google Maps is unavailable (network, API restriction, quota or billing). You can still enter addresses manually; no coordinates or distance will be guessed.'
export function loadGoogleMaps():Promise<MapLibraries>{
 if(loading)return loading
 const key=import.meta.env.VITE_GOOGLE_MAPS_BROWSER_KEY?.trim()
 if(!key)return Promise.reject(new Error('Maps browser key is not configured. Manual address entry is available.'))
 loading=new Promise<void>((resolve,reject)=>{
  if(window.google?.maps.importLibrary){resolve();return}
  const script=document.createElement('script');script.id='transivox-google-maps'
  const previous=window.gm_authFailure
  const fail=()=>{window.dispatchEvent(new Event('transivox-maps-error'));reject(new Error(mapFailure))}
  const timer=window.setTimeout(fail,15000)
  window.gm_authFailure=()=>{previous?.();window.clearTimeout(timer);fail()}
  window.transivoxMapsReady=()=>{window.clearTimeout(timer);resolve()}
  script.async=true;script.onerror=()=>{window.clearTimeout(timer);fail()}
  const params=new URLSearchParams({key,v:'weekly',loading:'async',callback:'transivoxMapsReady',auth_referrer_policy:'origin'})
  script.src='https://maps.googleapis.com/maps/api/js?'+params.toString();document.head.append(script)
 }).then(async()=>{
  if(!window.google?.maps.importLibrary)throw new Error(mapFailure)
  const [maps,places,marker]=await Promise.all(['maps','places','marker'].map(n=>window.google!.maps.importLibrary(n)))
  return {maps,places,marker} as MapLibraries
 }).catch(()=>{loading=null;document.getElementById('transivox-google-maps')?.remove();throw new Error(mapFailure)})
 return loading
}
