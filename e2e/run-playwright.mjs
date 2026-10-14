import {spawnSync} from 'node:child_process'

const mode = process.argv[2]
const env = {...process.env}
const args = ['playwright', 'test']
if (mode === 'cross-browser') {
  env.E2E_CROSS_BROWSER = 'true'
  args.push('e2e/kyc.spec.ts')
} else if (mode === 'aws') {
  env.E2E_REAL_AWS = 'true'
  env.E2E_MANAGE_SERVERS = 'false'
  args.push('e2e/kyc.aws.spec.ts', '--project=chromium')
} else {
  throw new Error('Expected cross-browser or aws mode')
}
const command = process.platform === 'win32' ? 'npx.cmd' : 'npx'
const result = spawnSync(command, args, {stdio: 'inherit', env})
process.exit(result.status ?? 1)
