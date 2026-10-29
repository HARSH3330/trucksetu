import {expect,it} from 'vitest'
import * as types from './demand-types'

it('distinguishes a recorded refund obligation from completed processing',()=>{
 const message=(types as unknown as {connectionRefundMessage?:(status:string,amount:string)=>string}).connectionRefundMessage
 expect(message,'Persistent refund state needs honest customer copy').toBeTypeOf('function')
 if(!message)return
 expect(message('requested','1200')).toContain('requested')
 expect(message('requested','1200')).not.toContain('processed')
 expect(message('pending','1200')).toContain('pending')
 expect(message('unknown','1200')).toContain('not confirmed')
 expect(message('failed','1200')).toContain('remains open')
 expect(message('processed','1200')).toContain('recorded as processed')
 expect(message('no_captured_payment','0')).toContain('No captured')
})
