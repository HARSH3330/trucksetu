# Local KYC review coverage

`npm run e2e` runs the original provider journey and two independent review scenarios in Chromium. All browser actors authenticate normally. Each review scenario creates fresh provider A/B accounts and uses the dedicated seeded administrator. External storage/scanning alone is simulated.

The review scenarios cover protected signed downloads and exact uploaded bytes, unauthenticated denial, approval with no/some/all document acceptances, persisted verification and provider UI reload, correction via `resubmit_required`, retained review reasons, rejected historical document exclusion, terminal rejection, and cross-provider/admin API denial with unchanged database snapshots. Required owner documents are read from the actual backend rules. Snapshots use the guarded, read-only `e2e_inspect` helper.

Workflow limits: `rejected` is terminal; correction/resubmission uses `resubmit_required`. There is no application-by-ID GET or independent document-acceptance endpoint. The by-ID 404 probe therefore does not prove ownership enforcement on such a route. Admin review is exercised through authenticated protected APIs, not the admin UI/navigation. Provider status and correction reasons are exercised in the UI.

The fake download endpoint is local-test-only, signed, expires after 300 seconds and requires a clean simulated scan. A signed URL is a short-lived bearer capability, not a public document. These tests do not verify S3 or GuardDuty.

## Windows PowerShell

From the repository root, with the isolated PostgreSQL database/user already provisioned:

```powershell
$env:APP_ENV = 'test'
$env:TRANSIVOX_E2E = 'true'
$env:E2E_REAL_AWS = 'false'
$env:PYTHONPATH = 'backend'
$env:E2E_PYTHON = (Resolve-Path '.\.venv\Scripts\python.exe').Path
# Set privately using the restricted local test user's connection string:
$env:E2E_DATABASE_URL = 'postgresql+psycopg://TEST_USER:TEST_PASSWORD@127.0.0.1:5432/transivox_e2e'
& $env:E2E_PYTHON -m pytest backend/tests/test_kyc_review_regression.py backend/tests/test_e2e_storage_support.py backend/tests/test_e2e_database_safety.py backend/tests/test_phase12.py -q -p no:cacheprovider
npm run e2e
npx playwright show-report
```

Replace the URL placeholders locally; never share credentials. Retain the existing host allowlist safeguard and database-scoped user permissions. No application database fallback is permitted. The local run resets only the guarded `transivox_e2e` database and applies real migrations. Account credentials remain configurable using the existing E2E account variables; defaults use `provider.e2e@example.com` and `admin.e2e@example.com`.

Run the real asynchronous serialization regression separately with the same guarded environment:

```powershell
& $env:E2E_PYTHON -m pytest backend/tests/integration/test_kyc_serialization.py -q -p no:cacheprovider
```
