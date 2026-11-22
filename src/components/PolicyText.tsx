import {Fragment,type ReactNode} from 'react'

/** Renders the small Markdown subset used by legal documents: headings, bold, bullet lists and paragraphs. */
function inline(text:string):ReactNode[]{return text.split(/\*\*(.+?)\*\*/g).map((part,index)=>index%2?<strong key={index}>{part}</strong>:part)}

export default function PolicyText({content}:{content:string}){
  const blocks=content.replace(/\r\n/g,'\n').split(/\n{2,}/).map(block=>block.trim()).filter(Boolean)
  return <div className="policy-content">{blocks.map((block,index)=>{
    if(block.startsWith('## '))return <h3 key={index}>{inline(block.slice(3))}</h3>
    if(block.startsWith('# '))return <h2 key={index}>{inline(block.slice(2))}</h2>
    const lines=block.split('\n')
    if(lines.every(line=>line.startsWith('* ')))return <ul key={index}>{lines.map((line,item)=><li key={item}>{inline(line.slice(2))}</li>)}</ul>
    return <p key={index}>{lines.map((line,item)=><Fragment key={item}>{item>0&&<br/>}{inline(line)}</Fragment>)}</p>
  })}</div>
}
