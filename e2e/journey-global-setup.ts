import {spawnSync} from 'node:child_process'
import path from 'node:path'
import {validateE2EEnvironment} from './safety'
export default function setup(){
 const safe=validateE2EEnvironment(process.env)
 const result=spawnSync(process.env.E2E_PYTHON||'python',['e2e_journey_guard.py'],{cwd:path.resolve('backend'),env:{...process.env,APP_ENV:'test',TRANSIVOX_E2E:'true',DATABASE_URL:safe.databaseUrl},stdio:'inherit',shell:false})
 if(result.status!==0)throw Error('Existing isolated DB guard failed; no reset or fallback is permitted')
}
