import {type FieldFormat,formatWarning} from '../lib/field-formats'

/** Shows the expected format under an input, and what to fix once the typed value would be refused. Link it with aria-describedby={id}. */
export default function FormatHint({id,format,value}:{id:string;format:FieldFormat;value:string}){
  const warning=formatWarning(format,value)
  return <small id={id} className={warning?'format-hint format-warning':'format-hint'} aria-live="polite">{warning?<><strong>Check format:</strong> {warning}</>:format.hint}</small>
}
