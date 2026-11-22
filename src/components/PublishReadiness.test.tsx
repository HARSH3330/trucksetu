import React from 'react'
import {renderToStaticMarkup} from 'react-dom/server'
import {describe,expect,it} from 'vitest'
import PublishReadiness,{PublishBlockedNotice} from './PublishReadiness'

const user={id:'u1',full_name:'Fictional Customer',roles:['customer'],email:'fictional@example.com',email_verified:false,mobile:'+919999999999',mobile_verified:true}

describe('publish readiness box',()=>{
  it('lists each remaining step with its own next action',()=>{
    const html=renderToStaticMarkup(<PublishReadiness user={{...user,mobile_verified:false}} kycStatus="under_review" onVerify={()=>{}} onAccountHelp={()=>{}}/>)
    expect(html).toContain('Before you can publish')
    expect(html).toContain('verify your email or phone (one is enough) and complete the PAN review')
    expect(html).toContain('Email address:')
    expect(html).toContain('Phone number:')
    expect(html).toContain('PAN review:')
    expect(html).toContain('a reviewer is checking it')
    expect(html).toMatch(/<button[^>]*>Verify email or phone<\/button>/)
    expect(html).toMatch(/<button[^>]*>PAN verification<\/button>/)
  })
  it('only offers the step that is actually missing',()=>{
    const html=renderToStaticMarkup(<PublishReadiness user={user} kycStatus={null} onVerify={()=>{}} onAccountHelp={()=>{}}/>)
    expect(html).not.toContain('Verify email or phone')
    expect(html).toContain('PAN verification')
    expect(html).toContain('optional, your phone is verified')
  })
  it('disappears once the account can publish',()=>{
    expect(renderToStaticMarkup(<PublishReadiness user={user} kycStatus="verified"/>)).toBe('')
  })
})

describe('publish blocked notice beside the Publish button',()=>{
  it('says plainly that the requirement cannot be posted until the account is verified',()=>{
    const html=renderToStaticMarkup(<PublishBlockedNotice user={{...user,mobile_verified:false}} kycStatus={null} onVerify={()=>{}} onAccountHelp={()=>{}}/>)
    expect(html).toContain('role="alert"')
    expect(html).toContain('You cannot post this requirement yet')
    expect(html).toContain('Email or phone: not verified')
    expect(html).toContain('PAN review: not started')
    expect(html).toMatch(/<button[^>]*>Verify email or phone<\/button>/)
    expect(html).toMatch(/<button[^>]*>PAN verification<\/button>/)
  })
  it('shows nothing while the PAN status is loading or once the account is ready',()=>{
    expect(renderToStaticMarkup(<PublishBlockedNotice user={user} kycStatus={undefined}/>)).toBe('')
    expect(renderToStaticMarkup(<PublishBlockedNotice user={user} kycStatus="verified"/>)).toBe('')
  })
})
