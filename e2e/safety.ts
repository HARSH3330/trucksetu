export type E2EEnvironment = {
  databaseUrl: string
  databaseHost: string
  databaseName: 'transivox_e2e'
  allowedDatabaseHosts: string[]
  realAws: boolean
}

const trueValues = new Set(['1', 'true', 'yes', 'on'])
const localTestHosts = new Set(['127.0.0.1', 'localhost', '::1', '[::1]', 'postgres'])

export function validateE2EEnvironment(env: NodeJS.ProcessEnv): E2EEnvironment {
  const rawUrl = env.E2E_DATABASE_URL?.trim()
  if (!rawUrl) throw new Error('E2E_DATABASE_URL is required; application database URLs are never used as a fallback')

  let url: URL
  try { url = new URL(rawUrl) } catch { throw new Error('E2E_DATABASE_URL must be a valid PostgreSQL URL') }
  if (!['postgresql:', 'postgres:'].includes(url.protocol)) throw new Error('E2E_DATABASE_URL must use PostgreSQL')

  const databaseName = decodeURIComponent(url.pathname.replace(/^\//, ''))
  if (databaseName !== 'transivox_e2e') throw new Error('E2E database name must be exactly transivox_e2e')

  const allowedDatabaseHosts = (env.E2E_ALLOWED_DATABASE_HOSTS ?? '')
    .split(',').map(host => host.trim().toLowerCase()).filter(Boolean)
  if (!allowedDatabaseHosts.length) throw new Error('E2E_ALLOWED_DATABASE_HOSTS must explicitly list local/test hosts')
  const databaseHost = url.hostname.toLowerCase()
  if (!allowedDatabaseHosts.includes(databaseHost)) throw new Error(`E2E database host ${databaseHost} is not explicitly allowed`)
  if (!localTestHosts.has(databaseHost)) throw new Error(`E2E database host ${databaseHost} is not a recognized local test host`)

  const realAws = trueValues.has((env.E2E_REAL_AWS ?? '').trim().toLowerCase())
  if (realAws) throw new Error('Real AWS/staging mode never resets or migrates a database; use the non-resetting AWS Playwright project')

  return {databaseUrl: rawUrl, databaseHost, databaseName: 'transivox_e2e', allowedDatabaseHosts, realAws}
}
