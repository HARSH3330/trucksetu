import React from 'react'
import {renderToStaticMarkup} from 'react-dom/server'
import {describe,expect,it} from 'vitest'
import VerificationCard,{VerificationBox,verificationState} from './VerificationCard'

describe('customer verification box',()=>{
  it('turns every server status into a plain next step',()=>{
    expect(verificationState(null)).toMatchObject({label:'Not started',step:0,action:'Start verification'})
    expect(verificationState('registered')).toMatchObject({label:'Upload your PAN',step:0,action:'Continue verification'})
    expect(verificationState('under_review')).toMatchObject({label:'Under review',step:2,action:'View status'})
    expect(verificationState('verified')).toMatchObject({label:'Verified',step:4,tone:'ok'})
    expect(verificationState('resubmit_required')).toMatchObject({label:'Action needed',tone:'warn',action:'Upload again'})
    expect(verificationState('rejected')).toMatchObject({label:'Not approved',tone:'bad'})
  })
  it('is a labelled box with progress and one clear button',()=>{
    const html=renderToStaticMarkup(<VerificationBox status="under_review" reason={null} signedIn onOpen={()=>{}}/>)
    expect(html).toContain('aria-labelledby="verification-title"')
    expect(html).toContain('Under review')
    expect(html).toMatch(/<li[^>]*aria-current="step"[^>]*>.*Manual review/)
    expect(html).toMatch(/<button[^>]*>View status<\/button>/)
  })
  it('asks signed-out visitors to sign in first',()=>{
    expect(renderToStaticMarkup(<VerificationBox status={null} reason={null} signedIn={false} onOpen={()=>{}}/>)).toMatch(/<button[^>]*>Sign in to verify<\/button>/)
  })
})

describe('loading the box safely',()=>{
  const card=(props:Partial<React.ComponentProps<typeof VerificationCard>>)=>renderToStaticMarkup(<VerificationCard user={null} onOpen={()=>{}} onSignIn={()=>{}} {...props}/>)
  it('renders nothing while the sign-in is still being restored',()=>{
    expect(card({sessionLoading:true})).toBe('')
  })
  it('shows the sign-in version to visitors without asking the server',()=>{
    expect(card({})).toMatch(/Sign in to verify/)
  })
  it('stays hidden for truck owners, drivers and admins',()=>{
    expect(card({user:{id:'f',full_name:'Fictional',roles:['provider']}})).toBe('')
  })
})
