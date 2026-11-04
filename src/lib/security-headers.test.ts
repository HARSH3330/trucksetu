import vercelJson from '../../vercel.json?raw'
import {expect,it} from 'vitest'

it('serves the frontend with anti-framing and content-sniffing headers',()=>{
  const config=JSON.parse(vercelJson)
  const headers=Object.fromEntries(config.headers.find((rule:{source:string})=>rule.source==='/(.*)').headers.map((item:{key:string;value:string})=>[item.key,item.value]))
  expect(headers['X-Frame-Options']).toBe('DENY')
  expect(headers['Content-Security-Policy']).toBe("frame-ancestors 'none'")
  expect(headers['X-Content-Type-Options']).toBe('nosniff')
  expect(headers['Referrer-Policy']).toBe('strict-origin-when-cross-origin')
  expect(config.git.deploymentEnabled['release/customer-first-20261026']).toBe(false)
})
