import {renderToStaticMarkup} from 'react-dom/server'
import {describe,expect,it} from 'vitest'
import PolicyText from './PolicyText'
import {PublicPolicy} from './PublicInformation'

const SAMPLE='# TERMS & CONDITIONS\n\n**Version:** v2\n\nWelcome to **TransivoX** ("Platform").\n\n## 1. About\n\n* Submit requirements;\n* Receive quotations.\n'

describe('policy text',()=>{
  it('shows headings, bold text and lists without raw formatting symbols',()=>{
    const html=renderToStaticMarkup(<PolicyText content={SAMPLE}/>)
    expect(html).toContain('<h2>TERMS &amp; CONDITIONS</h2>')
    expect(html).toContain('<h3>1. About</h3>')
    expect(html).toContain('<strong>TransivoX</strong>')
    expect(html).toMatch(/<ul><li>Submit requirements;<\/li><li>Receive quotations.<\/li><\/ul>/)
    expect(html).not.toMatch(/#|\*\*|^\* /m)
  })
  it('no longer labels the privacy notice a draft',()=>{
    expect(renderToStaticMarkup(<PublicPolicy kind="privacy"/>)).not.toContain('Draft pending legal review')
  })
})
