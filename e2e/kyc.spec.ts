import {expect, test, type Page} from '@playwright/test'
import {adminAccount, providerAccount} from './fixtures/accounts'
import {accessToken, captureApiFailures, signIn} from './fixtures/api'
import {createIdentityTestPdf} from './fixtures/pdf'

const apiBase = (process.env.E2E_API_URL || 'http://127.0.0.1:8000/api/v1').replace(/\/$/, '')
const apiOrigin = new URL(apiBase).origin
const controlToken = process.env.E2E_CONTROL_TOKEN || 'transivox-e2e-control-token'

async function uploadAndClean(page: Page, documentLabel: string, documentType: string, runId: string) {
  await page.getByLabel('Document type').selectOption(documentType)
  await page.getByLabel('File').setInputFiles({name: `${documentType}-fictional.pdf`, mimeType: 'application/pdf', buffer: createIdentityTestPdf(documentLabel, runId)})
  const registration = page.waitForRequest(request => request.url().endsWith('/kyc/documents') && request.method() === 'POST')
  await page.getByRole('button', {name: 'Upload securely'}).click()
  const storageKey = (await registration).postDataJSON().storage_key as string
  await expect(page.getByText(/GuardDuty is still scanning/)).toBeVisible()
  const clean = await page.request.post(`${apiOrigin}/__e2e__/scan/clean`, {headers: {'X-E2E-Control-Token': controlToken}, data: {storage_key: storageKey}})
  expect(clean.ok()).toBeTruthy()
  await page.getByRole('button', {name: 'Check scan again'}).click()
  await expect(page.getByText('Document passed malware scanning and was registered.')).toBeVisible()
}

test('provider KYC blocks pending files, validates required files, and reaches under_review', async ({browser}, testInfo) => {
  const providerContext = await browser.newContext({recordVideo:{dir:testInfo.outputPath('provider-video')}})
  const providerPage = await providerContext.newPage()
  captureApiFailures(providerPage)
  let adminContext: Awaited<ReturnType<typeof browser.newContext>> | undefined
  let failed=false
  try {
  await signIn(providerPage, providerAccount.email, providerAccount.password)
  await providerPage.getByRole('button', {name: 'Verification status'}).click()
  await expect(providerPage.getByRole('heading', {name: 'Start provider verification'})).toBeVisible()
  await providerPage.getByLabel('Legal name').fill('TransivoX Fictional Test Provider')
  await providerPage.getByLabel('Verification type').selectOption('owner')
  await providerPage.getByLabel('PAN last four characters').fill('T123')
  const applicationResponse=providerPage.waitForResponse(response=>new URL(response.url()).pathname.endsWith('/kyc/applications')&&response.request().method()==='POST')
  await providerPage.getByRole('button', {name: /Create application/}).click()
  expect((await applicationResponse).status(),'Create KYC application API response; inspect redacted diagnostics above').toBe(201)
  await expect(providerPage.getByRole('heading', {name: 'Your KYC application'})).toBeVisible()

  await uploadAndClean(providerPage, 'Aadhaar', 'aadhaar', testInfo.testId)
  await providerPage.getByRole('button', {name: 'Submit for review'}).click()
  await expect(providerPage.getByText(/Required documents are missing/)).toBeVisible()
  await uploadAndClean(providerPage, 'PAN', 'pan', testInfo.testId)
  await uploadAndClean(providerPage, 'Vehicle RC', 'vehicle_rc', testInfo.testId)
  await providerPage.getByRole('button', {name: 'Submit for review'}).click()
  await expect(providerPage.getByText('Application submitted for manual review.')).toBeVisible()
  await expect(providerPage.getByText('under review', {exact: true})).toBeVisible()

  adminContext = await browser.newContext({recordVideo:{dir:testInfo.outputPath('admin-video')}})
  const adminPage = await adminContext.newPage()
  captureApiFailures(adminPage)
  await signIn(adminPage, adminAccount.email, adminAccount.password)
  const adminToken = await accessToken(adminPage)
  expect(adminToken).not.toBe('')
  const queue = await adminContext.request.get(`${apiBase}/kyc/admin/applications?status=under_review`, {headers: {Authorization: `Bearer ${adminToken}`}})
  expect(queue.ok()).toBeTruthy()
  const applications = await queue.json() as Array<{legal_name: string; status: string; documents: unknown[]}>
  expect(applications).toEqual(expect.arrayContaining([expect.objectContaining({legal_name: 'TransivoX Fictional Test Provider', status: 'under_review'})]))
  expect(applications.find(item => item.legal_name === 'TransivoX Fictional Test Provider')?.documents).toHaveLength(3)
  } catch(error) {
    failed=true
    throw error
  } finally {
    if(failed){
      for(const [index,page] of [...providerContext.pages(),...(adminContext?.pages()||[])].entries()){
        await page.screenshot({path:testInfo.outputPath(`failure-${index}.png`)}).catch(()=>{
          console.error(`Failure screenshot ${index} could not be captured; original test error is preserved.`)
        })
      }
    }
    // Attempt both closures even if one fails. Preserve the journey's original
    // exception, but report cleanup failure and fail an otherwise successful run.
    const cleanup=await Promise.allSettled([
      ...(adminContext?[adminContext.close()]:[]),providerContext.close(),
    ])
    const cleanupFailures=cleanup.filter(result=>result.status==='rejected')
    if(cleanupFailures.length){
      if(failed)console.error(`${cleanupFailures.length} browser context cleanup operation(s) failed; original test error is preserved.`)
      else throw new Error(`${cleanupFailures.length} browser context cleanup operation(s) failed after the KYC assertions.`)
    }
  }
})
