import {describe, expect, it} from 'vitest'
import {validateE2EEnvironment} from './safety'

const safe = {
  E2E_DATABASE_URL: 'postgresql://transivox_e2e_user:secret@127.0.0.1:5432/transivox_e2e',
  E2E_ALLOWED_DATABASE_HOSTS: '127.0.0.1,localhost',
}

describe('E2E database safety', () => {
  it('requires the dedicated URL and never falls back to DATABASE_URL', () => {
    expect(() => validateE2EEnvironment({...safe, E2E_DATABASE_URL: undefined, DATABASE_URL: safe.E2E_DATABASE_URL})).toThrow(/E2E_DATABASE_URL is required/)
  })

  it.each([
    'postgresql://u:p@127.0.0.1/transivox_test',
    'postgresql://u:p@127.0.0.1/my_transivox_e2e',
    'postgresql://u:p@127.0.0.1/transivox_e2e%20',
  ])('rejects every database name except the exact dedicated name: %s', url => {
    expect(() => validateE2EEnvironment({...safe, E2E_DATABASE_URL: url})).toThrow(/exactly transivox_e2e/)
  })

  it('rejects non-PostgreSQL URLs', () => {
    expect(() => validateE2EEnvironment({...safe, E2E_DATABASE_URL: 'mysql://u:p@127.0.0.1/transivox_e2e'})).toThrow(/PostgreSQL/)
  })

  it('uses exact hostname matching', () => {
    expect(() => validateE2EEnvironment({...safe, E2E_DATABASE_URL: 'postgresql://u:p@localhost.attacker.test/transivox_e2e'})).toThrow(/explicitly allowed/)
  })

  it('rejects a public host even when an operator lists it', () => {
    expect(() => validateE2EEnvironment({
      ...safe,
      E2E_DATABASE_URL: 'postgresql://u:p@database.example.com/transivox_e2e',
      E2E_ALLOWED_DATABASE_HOSTS: 'database.example.com',
    })).toThrow(/local test host/)
  })

  it('accepts the exact database and an explicitly allowed host', () => {
    expect(validateE2EEnvironment(safe)).toMatchObject({databaseName: 'transivox_e2e', databaseHost: '127.0.0.1', realAws: false})
  })

  it('forbids reset mode when real AWS mode is enabled', () => {
    expect(() => validateE2EEnvironment({...safe, E2E_REAL_AWS: 'true'})).toThrow(/never resets/)
  })
})
