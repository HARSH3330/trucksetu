import {expect, test} from '@playwright/test'
import {providerAccount} from './fixtures/accounts'
import {signIn} from './fixtures/api'
import {createIdentityTestPdf} from './fixtures/pdf'

test('real S3 upload receives an actual clean GuardDuty result', async ({page}, testInfo) => {
  for (const name of ['E2E_WEB_URL', 'E2E_API_URL', 'E2E_PROVIDER_EMAIL', 'E2E_PROVIDER_PASSWORD']) {
    expect(process.env[name], `${name} is required for the opt-in AWS test`).toBeTruthy()
  }
  await signIn(page, providerAccount.email, providerAccount.password)
  await page.getByRole('button', {name: 'Verification status'}).click()
  if (await page.getByRole('heading', {name: 'Start provider verification'}).isVisible()) {
    await page.getByLabel('Legal name').fill(`TransivoX AWS Test ${Date.now()}`)
    await page.getByLabel('Verification type').selectOption('owner')
    await page.getByRole('button', {name: /Create application/}).click()
  }
  await page.getByLabel('Document type').selectOption('aadhaar')
  await page.getByLabel('File').setInputFiles({name: 'aws-aadhaar-fictional.pdf', mimeType: 'application/pdf', buffer: createIdentityTestPdf('Aadhaar', testInfo.testId)})
  await page.getByRole('button', {name: 'Upload securely'}).click()

  const timeoutMs = Number(process.env.E2E_AWS_SCAN_TIMEOUT_MS || 180_000)
  const deadline = Date.now() + timeoutMs
  while (Date.now() < deadline && await page.getByRole('button', {name: 'Check scan again'}).isVisible()) {
    await page.waitForTimeout(5_000)
    await page.getByRole('button', {name: 'Check scan again'}).click()
  }
  await expect(page.getByText('Document passed malware scanning and was registered.')).toBeVisible()
})
