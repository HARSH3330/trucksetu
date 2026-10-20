import {defineConfig, devices} from '@playwright/test'

const realAws = (process.env.E2E_REAL_AWS || '').toLowerCase() === 'true'
const crossBrowser = (process.env.E2E_CROSS_BROWSER || '').toLowerCase() === 'true'
const manageServers = (process.env.E2E_MANAGE_SERVERS || 'true').toLowerCase() !== 'false'
const webUrl = process.env.E2E_WEB_URL || 'http://127.0.0.1:5173'
const apiUrl = process.env.E2E_API_URL || 'http://127.0.0.1:8000/api/v1'
const apiOrigin = new URL(apiUrl).origin
const python = process.env.E2E_PYTHON || 'python'
const localEnvironment = {
  ...process.env,
  APP_ENV: 'test', TRANSIVOX_E2E: 'true',
  DATABASE_URL: process.env.E2E_DATABASE_URL || '', MIGRATION_DATABASE_URL: process.env.E2E_DATABASE_URL || '',
  E2E_API_ORIGIN: apiOrigin, E2E_WEB_URL: webUrl,
  ALLOWED_ORIGINS: new URL(webUrl).origin,
  E2E_CONTROL_TOKEN: process.env.E2E_CONTROL_TOKEN || 'transivox-e2e-control-token',
  SECRET_KEY: process.env.E2E_SECRET_KEY || 'e2e-only-secret-key-not-for-any-real-environment-0123456789',
  DEBUG: 'false', REDIS_REQUIRED: 'false',
}

export default defineConfig({
  testDir: './e2e',
  testMatch: realAws ? '**/*.aws.spec.ts' : ['**/kyc*.spec.ts','**/release-*.spec.ts'],
  testIgnore: realAws ? [] : ['**/*.aws.spec.ts'],
  fullyParallel: false,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: 1,
  reporter: [['list'], ['html', {outputFolder: 'playwright-report', open: 'never'}]],
  globalSetup: realAws ? undefined : './e2e/global-setup.ts',
  outputDir: 'test-results',
  use: {baseURL: webUrl, screenshot: 'only-on-failure', trace: 'retain-on-failure', video: 'retain-on-failure'},
  projects: [
    {name: 'chromium', use: {...devices['Desktop Chrome']}},
    ...(crossBrowser ? [{name: 'firefox', use: {...devices['Desktop Firefox']}}, {name: 'webkit', use: {...devices['Desktop Safari']}}] : []),
  ],
  webServer: realAws || !manageServers ? undefined : [
    {command: `"${python}" -m e2e_server --port ${new URL(apiOrigin).port || '8000'}`, cwd: './backend', url: `${apiOrigin}/health/live`, reuseExistingServer: false, env: localEnvironment, timeout: 120_000},
    // Serve the actual built client, avoiding dev-server HMR/optimizer reloads
    // during independent browser sessions. API and DB remain real and local.
    {command: `npm run build && npm run preview -- --host 127.0.0.1 --port ${new URL(webUrl).port || '5173'} --strictPort`, url: webUrl, reuseExistingServer: false, env: {...process.env, VITE_API_URL: apiUrl,VITE_MSG91_WIDGET_ID:'',VITE_MSG91_WIDGET_TOKEN_AUTH:''}, timeout: 120_000},
  ],
})
