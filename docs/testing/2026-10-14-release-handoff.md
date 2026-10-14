# Local release handoff — 2026-10-14

This checkout remains uncommitted/unpushed. No deployment, production migration, production data change, real SMS/email/payment or AWS operation was performed. Existing uncommitted KYC/Windows/scaffold changes were preserved.

## Delivered and verification boundaries

- Assigned-driver reads and actions; pickup/delivery OTP issue/verify UI, accepted-not-delivered messaging, injected sender, state/proof gates, locked counters and explicit commits/history.
- Authentication preflight before database resolution; request validation no longer echoes private submitted values.
- Failure-counter fixes, refresh-family rejection commits and administrator recovery access-version invalidation. Real PostgreSQL tests added, not verified here.
- Historical settlement responses use stored commission amounts/rates, with locked snapshot creation.
- Private vehicle uploads/review: five existing expiry-rule files, clean scan/signature/size enforcement, authorized short-lived access, audit events, replacement/rejection rules. S3 VersionId pins registered/reviewed/downloaded bytes. Bucket versioning is now required for new vehicle files. Suspension/rejection does not require constructing storage.
- Account recovery/email resend/code UI and SMTP adapter; mobile contact password confirmation; MSG91 widget/server phone-proof validation. Password sign-in and KYC permissions unchanged.
- Minimal server-searched/paginated user/booking browser, audited ordinary-account status action and session/supply revocation, links to existing operational screens. Privileged account management and full console remain incomplete.
- Live public loads/error/empty states and working logo navigation. Shared-capacity Model B remains in scope; no feature was silently removed.

See the appended status in `2026-10-13-release-review.md` and the implementation checklist. Checked implementation boxes do not mean deployed or integration-verified.

### Checks actually run

- Backend non-integration suite: **225 passed**, two deprecation warnings. The earlier 220-test coverage run reported 71%; coverage was not rerun after the phone-policy additions.
- Frontend: **38 passed**, production TypeScript/Vite build passed.
- Chromium: **7 passed** in the local public/widget suite; fake SDK/API, mobile sample, unchanged-phone verification copy, no SMS.
- Ruff/domain mypy, three YAML workflow parses, single-head/offline migrations and git diff whitespace checks passed.
- PostgreSQL/full KYC, real AWS/delivery/payment and GitHub execution remain blocked/unverified.
- Widget test fixture/overlay mistakes and application false-confirmation copy were fixed; no timeout increases or skipped assertions. Missing pytest-cov was installed as declared development tooling and the coverage rerun passed. Exact setup below is provided, but the container/database commands were not executed here.

## P0/P1 remaining launch gates

1. Configure the exact isolated test database and run the new real-transaction regressions plus full KYC/multi-role journeys. Current `E2E_DATABASE_URL` is absent; no normal database fallback was used.
2. Verified-only phone exclusivity is approved and implemented. Run migration `20261014_22` and real concurrent-ownership/migration regressions in the isolated database. Migration refuses conflicting or invalid verified claims without choosing an owner; any such deployment conflict requires explicit remediation. No silent reassignment was implemented.
3. Review legacy approved-vehicle backfill/reapproval policy and required-file rollout. Existing metadata approvals were not automatically revoked. Provider KYC still uses its legacy key-only storage references; bind its reviewed bytes to immutable versions before real-storage launch. Local KYC passing is not proof of this S3 invariant.
4. Finish shared-capacity publication/evaluation/reservation/consent/shared-booking UI and real concurrency/expiry-release checks. No full-vehicle-only pilot scope was selected.
5. Verify real private storage versioning/IAM/version-specific scan tagging and signed downloads; MSG91 widget/accepted trip template and delivery receipts; SMTP actual delivery; Maps runtime. Local fake results are not live-provider evidence.
6. Perform sandbox captured-payment/webhook/replay/refund/invoice/settlement reconciliation and approve financial/tax/business policies.
7. Complete operator/supply-reactivation workflows, mobile multi-role journeys, deployed configuration, operational alerts, backup restoration, independent security and qualified legal/privacy/tax reviews.

Not public-launch ready. Staging verification is conditional on local DB/migration/CI checks and explicit staging authorization. No staging/live use is authorized by this document.

## Windows PostgreSQL setup

If your previously approved `transivox_e2e` database already exists, do not recreate it. Privately configure its URL and use the checks below. The user must be limited to that local test database, not a Neon/development administrator.

Otherwise, the following optional Docker setup creates a **new isolated local PostgreSQL server**. It requires Docker Desktop. It does not touch existing PostgreSQL or Neon. Do not reuse an existing container name without inspecting it.

```powershell
cd 'C:\Users\harsh\OneDrive\Desktop\english learning\logistic\trucksetu'
docker ps -a --filter 'name=transivox-e2e-postgres'
# Stop here if that container already exists; inspect/reuse the intended one.
$taskAdminSecret=Read-Host 'New LOCAL test PostgreSQL administrator password' -AsSecureString
$env:POSTGRES_PASSWORD=[Net.NetworkCredential]::new('', $taskAdminSecret).Password
docker run --name transivox-e2e-postgres -e POSTGRES_PASSWORD -p 127.0.0.1:55432:5432 -d postgres:16
Remove-Item Env:POSTGRES_PASSWORD
$taskAdminSecret=$null
docker exec -it transivox-e2e-postgres psql -U postgres -d postgres
```

Inside this **new isolated container only**, run:

```sql
CREATE ROLE transivox_e2e_user LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION;
\password transivox_e2e_user
CREATE DATABASE transivox_e2e OWNER transivox_e2e_user;
REVOKE CONNECT ON DATABASE postgres FROM PUBLIC;
REVOKE CONNECT ON DATABASE template1 FROM PUBLIC;
\q
```

The password command prompts privately. Do NOT apply these PUBLIC revocations to a shared/development/production server. Runtime tests must use `transivox_e2e_user`, not `postgres`. The URL is `postgresql://transivox_e2e_user:<URL-encoded-test-password>@127.0.0.1:55432/transivox_e2e`; enter it privately below, never in chat. For an existing approved local server use its actual port, database/user safeguards unchanged.

## Guarded migrations, regressions and KYC rerun

```powershell
cd 'C:\Users\harsh\OneDrive\Desktop\english learning\logistic\trucksetu'
$env:APP_ENV='test'
$env:TRANSIVOX_E2E='true'
$env:E2E_REAL_AWS='false'
$env:E2E_ALLOWED_DATABASE_HOSTS='127.0.0.1'
$env:E2E_CONTROL_TOKEN='local-only-regression-control'
$env:SECRET_KEY='local-regression-only-never-production-012345678901234567890123456789'
$env:PYTHONPATH='backend'
$env:E2E_PYTHON=(Resolve-Path '.\.venv\Scripts\python.exe').Path
$taskDbSecret=Read-Host 'Dedicated LOCAL transivox_e2e URL' -AsSecureString
$env:E2E_DATABASE_URL=[Net.NetworkCredential]::new('', $taskDbSecret).Password
$taskDbSecret=$null

& $env:E2E_PYTHON -m e2e_database validate
if($LASTEXITCODE -ne 0){throw 'Test database safety validation failed; do not migrate or reset.'}
$env:DATABASE_URL=$env:E2E_DATABASE_URL
$env:MIGRATION_DATABASE_URL=$env:E2E_DATABASE_URL
Push-Location backend
try {
  & $env:E2E_PYTHON -m alembic -c alembic.ini upgrade head
  if($LASTEXITCODE -ne 0){throw 'Dedicated test migration failed.'}
} finally { Pop-Location }

& $env:E2E_PYTHON -m pytest backend/tests/integration/test_kyc_serialization.py backend/tests/integration/test_release_counter_persistence.py backend/tests/integration/test_phone_widget_database.py backend/tests/integration/test_verified_phone_migration.py -q -p no:cacheprovider
if($LASTEXITCODE -ne 0){throw 'PostgreSQL regressions failed; inspect redacted output before proceeding.'}
npm run e2e
npx playwright show-report
```

The KYC command intentionally resets ONLY the guarded `transivox_e2e` database and applies real migrations/seeds again. NEVER set the URL to another database or staging/AWS mode. The local E2E server validates before importing app settings and explicitly binds both database variables. Windows selector-loop and Alembic percent escaping remain intact.

Three new migrations require review/application in the isolated DB: `20261013_20` session versions, `20261013_21` version-pinned private vehicle records, and `20261014_22` verified-only canonical phone ownership. The last replaces all-account phone uniqueness with a verified-only unique index and refuses ambiguous verified records; downgrade refuses duplicate claims. None ran on any database here. Single-head/offline SQL checks passed at head `20261014_22`. Do not run production migrations automatically; production release/backups need separate approval.

## Database-independent checks

```powershell
$env:APP_ENV='test'
$env:TRANSIVOX_E2E='true'
$env:E2E_REAL_AWS='false'
$env:E2E_CONTROL_TOKEN='local-only-regression-control'
$env:SECRET_KEY='local-regression-only-never-production-012345678901234567890123456789'
$env:PYTHONPATH='backend'
& .\.venv\Scripts\python.exe -m pytest backend/tests --ignore=backend/tests/integration -q -p no:cacheprovider
& .\.venv\Scripts\python.exe -m ruff check backend/app backend/tests backend/migrations --config backend/pyproject.toml
& .\.venv\Scripts\python.exe -m mypy backend/app/domain.py --ignore-missing-imports
npm test
npm run build
npx playwright test --config playwright.public.config.ts
npx playwright show-report playwright-public-report
```

Public/widget browser tests use fake SDK/API boundaries and deliberate local-only configuration, including a 390px sample. They do not prove real password authentication, database persistence, MSG91, S3 or GuardDuty. Browser traces/screenshots are retained on failures. See `2026-10-14-msg91-widget.md` for exact frontend/API local and Vercel environment names.

## Owner setup after local gates

- Configure MSG91 widget-only public variables in the frontend and private account Authkey in the API. Real widget testing can send a paid SMS; do it only with explicit staging approval. The supplied widget token is not the account Authkey.
- For vehicle files: bucket public access blocked, encryption/versioning enabled, scan tags on exact versions. Least-privilege API identity needs version-read/tag permissions (`s3:GetObjectVersion`, `s3:GetObjectVersionTagging`) as well as existing upload/read operations. Lifecycle must not delete accepted versions while records require access. This configuration was not tested against AWS.
- The application/presigned-upload identity must not be allowed to forge malware-scan tags. Only the approved scanner should write the clean-result tags. This IAM gate and actual GuardDuty version tagging must be verified separately.
- SMTP verified sender, trip OTP DLT/template variable, restricted Maps key, Razorpay test webhook, alerts and backup restore: configure privately and verify each runtime operation, not just readiness.
- Finish entity/contact/legal/privacy/KYC retention/cancellation/tax rules with qualified advisers. No invented legal or financial claims are included.
