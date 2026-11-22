import {loadGoogleMaps,type PlacePrediction} from './google-maps'

export type PlaceValue={address:string;city:string;lat:number;lng:number}
export type Suggestion={id:string;main:string;secondary:string;prediction:PlacePrediction}
type Component={longText:string;types:string[]}

export const MIN_QUERY=3
export const shouldSearch=(text:string)=>text.trim().length>=MIN_QUERY

const CITY_TYPES=['locality','postal_town','administrative_area_level_3','administrative_area_level_2']
export function cityFromComponents(components:Component[]|undefined):string{
  for(const type of CITY_TYPES){const match=components?.find(item=>item.types.includes(type));if(match)return match.longText}
  return ''
}

export function nextOption(current:number,count:number,key:string):number{
  if(!count)return -1
  if(key==='Home')return 0
  if(key==='End')return count-1
  if(key==='ArrowDown')return current<0||current>=count-1?0:current+1
  if(key==='ArrowUp')return current<=0?count-1:current-1
  return current
}

/** One session token per typing session keeps Google billing to a single autocomplete session. */
export async function newSearchSession():Promise<unknown>{
  const sdk=await loadGoogleMaps()
  return new sdk.places.AutocompleteSessionToken()
}

export async function suggestPlaces(input:string,session:unknown,cities=false):Promise<Suggestion[]>{
  const sdk=await loadGoogleMaps()
  const result=await sdk.places.AutocompleteSuggestion.fetchAutocompleteSuggestions({input:input.trim(),sessionToken:session,includedRegionCodes:['in'],...(cities?{includedPrimaryTypes:['(cities)']}:{})})
  return result.suggestions.flatMap(item=>item.placePrediction?[{id:item.placePrediction.placeId,main:item.placePrediction.mainText?.text||item.placePrediction.text.text,secondary:item.placePrediction.secondaryText?.text||'',prediction:item.placePrediction}]:[])
}

export async function resolveSuggestion(suggestion:Suggestion):Promise<PlaceValue>{
  const place=suggestion.prediction.toPlace()
  await place.fetchFields({fields:['formattedAddress','location','addressComponents']})
  if(!place.location||!place.formattedAddress)throw new Error('Place details are unavailable')
  return {address:place.formattedAddress,city:cityFromComponents(place.addressComponents),lat:place.location.lat(),lng:place.location.lng()}
}
