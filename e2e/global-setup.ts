import {spawnSync} from 'node:child_process'
import path from 'node:path'
import {validateE2EEnvironment} from './safety'

function run(command: string, args: string[], cwd: string, env: NodeJS.ProcessEnv) {
  const result = spawnSync(command, args, {cwd, env, stdio: 'inherit', shell: false})
  if (result.error) throw result.error
  if (result.status !== 0) throw new Error(`${command} ${args.join(' ')} failed with exit code ${result.status}`)
}

export default async function globalSetup() {
  if ((process.env.E2E_REAL_AWS ?? '').toLowerCase() === 'true') return
  const safe = validateE2EEnvironment(process.env)
  const backend = path.resolve(process.cwd(), 'backend')
  const python = process.env.E2E_PYTHON?.trim() || 'python'
  const env = {
    ...process.env,
    APP_ENV: 'test',
    TRANSIVOX_E2E: 'true',
    DATABASE_URL: safe.databaseUrl,
    MIGRATION_DATABASE_URL: safe.databaseUrl,
  }
  run(python, ['-m', 'e2e_database', 'reset'], backend, env)
  run(python, ['-m', 'alembic', 'upgrade', 'head'], backend, env)
  run(python, ['-m', 'e2e_database', 'seed'], backend, env)
}
