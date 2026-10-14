# Playwright KYC End-to-End Test Design

**Date:** 2026-10-07
**Status:** Proposed for user review
**Scope:** Deterministic local KYC journey testing plus explicitly enabled staging/AWS integration checks

## Purpose

Create a repeatable Playwright test suite that verifies TransivoX's provider KYC journey across the real React interface, FastAPI routes, authorization rules, and PostgreSQL state. The default suite must be safe to run repeatedly on a developer machine or in CI without contacting production services. A separate, opt-in mode may verify real S3 uploads and GuardDuty malware-scan results in an isolated non-production AWS environment.

The suite will establish what the application does with scan results. The deterministic local mode cannot prove that AWS S3 or GuardDuty is correctly configured; only the explicitly enabled AWS integration suite can do that.

## Success Criteria

The suite must demonstrate all of the following:

1. A dedicated provider account can sign in through the actual frontend.
2. The provider can create an owner KYC application through the actual KYC screen.
3. Valid, harmless PDF fixtures are uploaded through the same presigned-upload flow used by the application.
4. Every generated PDF visibly states `NOT A REAL IDENTITY DOCUMENT` and contains no real identity data.
5. Document registration is rejected while the scan result is pending or otherwise not exactly `NO_THREATS_FOUND`.
6. Document registration succeeds only after the local fake scanner is deliberately changed to the clean result.
7. Submission fails while required owner documents are missing.
8. Aadhaar, PAN, and vehicle RC test documents can be registered after clean scans.
9. The complete application can be submitted and reaches `under_review`.
10. A separately authenticated administrator can confirm the application appears in the protected administrative review queue.
11. Failures preserve screenshots, traces, and useful report output without capturing real KYC data or secrets.

## Existing Product Boundaries

The design uses the current product contracts rather than inventing test-only business behavior:

- Frontend authentication is performed through the existing account modal and provider credentials.
- The provider opens **Verification status**, then uses the existing KYC controls and accessible labels.
- KYC calls use the existing `/api/v1/kyc` routes for application creation, private-upload creation, document registration, submission, and administrative listing.
- Owner applications require `aadhaar`, `pan`, and `vehicle_rc`.
- Storage acceptance remains fail-closed and requires the exact `GuardDutyMalwareScanStatus` value `NO_THREATS_FOUND`.
- Administrative queue verification uses the protected backend endpoint initially. A browser-level admin queue test can be added when the approved Marketplace Control Centre UI is implemented.

## Chosen Architecture

### 1. Playwright runner

The repository-level Playwright configuration will replace the generated starter configuration. It will provide:

- a configurable frontend base URL;
- Chromium as the default fast feedback project;
- optional Firefox and WebKit projects for deliberate cross-browser runs;
- screenshots on failure;
- traces retained on the first retry;
- video retained on failure;
- an HTML report;
- deterministic timeouts and retries appropriate to local and CI runs;
- a clearly separated real-AWS project or tag that never runs by default.

The existing `playwright.dev` sample will be removed and replaced with TransivoX tests.

### 2. Dedicated database with a hard safety gate

Local and CI KYC tests will require `E2E_DATABASE_URL`. There will be no fallback to `DATABASE_URL`, `MIGRATION_DATABASE_URL`, or any other application database variable.

Before any reset or migration, a safety validator will parse the URL and require all of these conditions:

- the database name is exactly `transivox_e2e`;
- the hostname matches an explicit allowlist supplied for local/test execution;
- local mode is active;
- staging/AWS mode is not active;
- the URL uses PostgreSQL;
- the connection is possible using a database user intended only for `transivox_e2e`.

A database name that merely contains `test`, `e2e`, or a similar substring is insufficient. The host check will use exact hostname matching, not substring matching. The default local allowlist will be limited to loopback/local container names documented by the test harness. CI may supply its exact PostgreSQL service hostname through an E2E-only allowlist variable.

The harness cannot prove PostgreSQL grants solely by inspecting a connection URL. Setup documentation will require a database user whose privileges are limited to `transivox_e2e`; the suite will also perform negative privilege checks where practical and fail if it can access a known non-test database.

The local harness may drop/recreate or truncate the isolated test schema only after all gates pass. It will then apply the real Alembic migration chain before starting the API. Staging and real-AWS modes will never run database reset code or automatic destructive cleanup.

### 3. Test-only storage and scan adapter

The production route layer currently constructs private storage directly. It will be refactored minimally to resolve storage through a dependency/factory while preserving production behavior. The production dependency continues to return the real `PrivateDocumentStorage` adapter.

The E2E support application will override only that dependency with an in-memory or temporary-directory adapter that implements the same contract:

- create a presigned-style upload target;
- accept the direct PDF upload;
- validate the declared MIME type, extension, size, and PDF signature through production validation code;
- report a pending scan by default;
- expose a test-control transition to `NO_THREATS_FOUND`;
- allow registration only when the production KYC route observes the exact clean result.

Test-control endpoints will exist only in the E2E support application. The production FastAPI entrypoint will neither import nor register them. The controls will additionally require local-test mode and a generated test control token. Production configuration will reject any attempt to enable this support app.

This boundary keeps application authorization, KYC validation, state changes, and submission logic real while replacing only the external AWS/GuardDuty behavior that ordinary tests must not call.

### 4. Accounts and isolated sessions

Global setup will seed two dedicated accounts in the freshly migrated E2E database:

- a provider account with the public provider role;
- an administrator account with the required review permission.

Credentials will come from E2E-only environment variables or safe local defaults that are unmistakably test credentials. They will never be reused for staging or production. Passwords, tokens, and storage URLs will not be printed in reports.

The provider journey and administrator verification will run in separate Playwright browser contexts. Provider authentication must occur through the real sign-in UI. Administrator authentication will use a separate session; until the admin KYC queue UI exists, that authenticated session will verify the protected administrative API response rather than pretending a missing interface was tested.

### 5. Harmless PDF generation

The test run will generate valid PDF files at runtime in Playwright's temporary output directory. Each page will include:

- `TRANSIVOX AUTOMATED TEST FIXTURE`;
- `NOT A REAL IDENTITY DOCUMENT` in prominent text;
- the fictional document type;
- a run identifier that contains no personal data.

No PDF will contain a real Aadhaar number, PAN, driving licence number, vehicle registration, address, photograph, signature, or user-provided identity data. Generated files and reports will be ignored by Git.

## Test Flow

### Deterministic local/CI scenario

1. Validate the E2E environment and database safety conditions.
2. Reset only `transivox_e2e` and apply the real Alembic migrations.
3. Start the E2E support FastAPI application and Vite frontend with test URLs.
4. Seed the dedicated provider and administrator accounts.
5. Open a provider browser context and sign in through the frontend.
6. Navigate to **Verification status** and create an owner KYC application.
7. Generate and upload the harmless Aadhaar PDF.
8. Attempt document registration while its scan is pending and assert the controlled rejection.
9. Mark that object `NO_THREATS_FOUND` through the authenticated local-only test control.
10. Retry registration and assert success.
11. Attempt submission and assert the required-document validation identifies the missing PAN and vehicle RC.
12. Upload, clean, and register the harmless PAN and vehicle RC PDFs.
13. Submit the application and assert its state is `under_review` in both the UI response and persisted API representation.
14. Open a completely separate administrator context, authenticate, and query the protected KYC review queue.
15. Assert that the submitted provider application is present and contains only expected metadata.

The core scenario will remain serial because each step deliberately advances one application through a state machine. Independent validation cases may run separately once they have isolated data.

### Opt-in staging/AWS scenario

Real storage verification will run only when an explicit flag such as `E2E_REAL_AWS=true` is set together with all required staging variables. It will require:

- a non-production frontend and API URL;
- dedicated staging provider and administrator accounts;
- a private non-production S3 bucket;
- GuardDuty malware protection configured for that bucket;
- a non-production database that the test does not reset;
- explicit cleanup behavior limited to test-created records/objects and safe identifiers.

This scenario will upload the same harmless PDFs using the real presigned S3 URL, poll through the public application behavior until GuardDuty produces a result, and verify registration succeeds only for the exact clean status. It will time out with a clear inconclusive/failure report if AWS does not produce a scan result within the configured limit.

The default test command, CI workflow, and local developer workflow will never enable this mode implicitly.

## Configuration Contract

The exact names may be refined during implementation, but the contract will distinguish the two modes clearly.

Required for deterministic local/CI mode:

- `E2E_DATABASE_URL`
- `E2E_ALLOWED_DATABASE_HOSTS`
- `E2E_WEB_URL` or a documented local default
- `E2E_API_URL` or a documented local default
- E2E-only provider and administrator credentials, or safe generated local defaults

Required in addition for real staging/AWS mode:

- `E2E_REAL_AWS=true`
- explicit staging frontend/API URLs
- dedicated staging provider/admin credentials
- AWS/storage variables required by the production adapter
- a scan polling timeout

Secret values will remain in environment variables and must not be committed. `.env.example` will document names and safe descriptions only.

## Error Handling and Diagnostics

The harness will fail before launching services if the database URL, database name, host allowlist, mode, or required variables are unsafe or ambiguous. Error messages will explain which safety condition failed without echoing credentials.

Tests will use role- and label-based selectors anchored to the real UI. Assertions will verify both visible user feedback and relevant API state. Expected pending-scan and missing-document rejections will be asserted by status and stable message/response fields rather than arbitrary sleeps.

On unexpected failure, Playwright will retain:

- a screenshot;
- a trace on retry;
- a failure video;
- the HTML report;
- sanitized service logs where available.

Artifacts must not contain authentication secrets, signed storage query strings, raw tokens, or real KYC material. The generated fictional PDFs may be retained because they contain no identity data, but they will not be committed.

## Commands and Reporting

Package scripts will provide clear entry points for:

- deterministic local KYC E2E tests;
- opening the Playwright HTML report;
- optional cross-browser execution;
- explicitly enabled real-AWS/staging execution.

The final implementation report will separate:

- behavior verified locally with simulated scan states;
- behavior verified through real AWS, if that opt-in run was authorized and configured;
- failures and their artifacts;
- checks that could not run and their exact missing prerequisites.

No result will describe S3 or GuardDuty as verified based only on the local fake adapter.

## CI Design

The Playwright workflow will run the deterministic suite with an isolated PostgreSQL service whose only test database is `transivox_e2e`. It will install frontend and backend dependencies, apply real migrations through the guarded setup, start the test support API and frontend, run Chromium, and upload the HTML report and failure artifacts.

The CI workflow will not receive production secrets and will not run real-AWS tests. A real-AWS workflow, if later desired, must be a separately approved manual workflow using a protected environment and dedicated non-production credentials.

## Security Boundaries

- There is no fallback from `E2E_DATABASE_URL` to an application database URL.
- Resets require the exact database name and an exact allowed host.
- Staging/AWS mode cannot invoke reset functions.
- Test storage controls are absent from the production app.
- Fake clean results cannot be supplied through a production endpoint.
- Dedicated test users and files contain no real identity information.
- Provider and administrator permissions remain enforced by production authorization code.
- Reports and logs redact secrets and signed upload URLs.
- Ordinary automated tests do not contact payment, messaging, email, production storage, or other live integrations.

## Out of Scope

- Proving that a real identity document is authentic.
- Testing malware detection with an actual malicious file.
- Treating the EICAR string as harmless; no malware-like fixture will be used in the standard suite.
- Implementing the administrative dashboard or KYC review UI.
- Running against production.
- Resetting, migrating, or cleaning a staging/AWS database automatically.
- Verifying real S3/GuardDuty behavior unless the opt-in AWS mode is deliberately configured and run.

## Acceptance Evidence

Implementation is acceptable when:

- unsafe database configurations are covered by focused tests and are rejected;
- the deterministic KYC Playwright scenario passes from a clean `transivox_e2e` database after real migrations;
- the pending-scan rejection, clean-scan success, missing-document rejection, and `under_review` transition are explicitly asserted;
- provider and admin sessions are demonstrably separate;
- the report contains screenshots/traces on an induced test failure;
- the HTML report is generated;
- the existing frontend and backend relevant test suites remain passing;
- real AWS behavior is reported as unverified unless the opt-in integration test actually ran successfully.
