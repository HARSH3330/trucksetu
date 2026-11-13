import {describe,expect,it} from 'vitest'
import {publishReadiness} from './publish-readiness'

const user={email:'fictional@example.com',email_verified:false,mobile:'+919999999999',mobile_verified:false}

describe('publish readiness',()=>{
  it('names everything still missing when nothing is verified',()=>{
    const result=publishReadiness(user,null)
    expect(result.ready).toBe(false)
    expect(result.summary).toBe('You cannot publish until you verify your email or phone (one is enough) and complete the PAN review.')
    expect(result.items.map(item=>[item.key,item.done])).toEqual([['email',false],['phone',false],['pan',false]])
    expect(result.items[0].detail).toContain('fictional@example.com')
    expect(result.items[1].detail).toContain('+919999999999')
    expect(result.items[2].detail).toBe('Not started')
  })
  it('treats one verified contact channel as enough and marks the other optional',()=>{
    const result=publishReadiness({...user,mobile_verified:true},'under_review')
    expect(result.summary).toBe('You cannot publish until you complete the PAN review.')
    expect(result.items[0].detail).toBe('Not verified (optional, your phone is verified)')
    expect(result.items[2].detail).toBe('Uploaded; a reviewer is checking it')
  })
  it('is ready only with a verified contact and an approved PAN',()=>{
    expect(publishReadiness({...user,email_verified:true},'verified')).toMatchObject({ready:true,summary:'Your account can publish requirements.'})
    expect(publishReadiness({...user,email_verified:true},'resubmit_required').ready).toBe(false)
    expect(publishReadiness(user,'verified').ready).toBe(false)
  })
  it('does not accuse the customer while the PAN status is still loading',()=>{
    const result=publishReadiness({...user,email_verified:true},undefined)
    expect(result).toMatchObject({ready:false,checking:true,summary:'Checking your verification status…'})
    expect(result.items[2].detail).toBe('Checking…')
  })
})
