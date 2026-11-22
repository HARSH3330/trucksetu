# Isolated PostgreSQL release verification — 19 October 2026

Local evidence only. No commit, push, deployment, production migration, SMS,
payment, AWS upload or paid service was authorized or performed for this task.

## Candidate and isolation

- HEAD: `d5f4306697518d7a1335482ce37f49f1d41c4f06`.
- Branch: `codex/release-candidate-hardening`; tested WITH the existing dirty
  working tree, not HEAD alone. See the accompanying source manifest for exact
  changed source paths and hashes. Documentation and generated artifacts are
  excluded from that executable-source fingerprint.
- Source manifest: `2026-10-19-postgres-source-manifest.json`, 59 changed/untracked
  code/configuration files; combined SHA256
  `e42ca95a0047606b895ea003243105085aefd7ce948e36a88aee3847f538060b`.
- Docker engine responded, version 29.8.2. Existing `stocz` containers/volumes
  were inspected by metadata only and preserved. Their ports 5432/8000 were not
  reused for this application. A separate test instance was created from the
  project's PostgreSQL 16 Alpine image.
- Container: `transivox-e2e-postgres`; volume: `transivox_e2e_postgres_data`;
  binding: `127.0.0.1:55432` only. Database: exactly `transivox_e2e`.
- Restricted owner: `transivox_e2e_user`; superuser/create-db/create-role/
  replication permissions all false. PUBLIC connect to postgres/template1 was
  revoked only inside this new dedicated instance.
- Test API: `http://127.0.0.1:18000`; built frontend: `http://127.0.0.1:5173`.
- Explicit `E2E_DATABASE_URL`, local-host allowlist, APP_ENV=test,
  TRANSIVOX_E2E=true and E2E_REAL_AWS=false were enforced. Application/migration
  URLs were set only AFTER validation, from the same guarded test URL. No fallback.
- Local generated credentials are retained encrypted with Windows DPAPI in the
  Git-ignored `.tmp/e2e-postgres-credential.xml`, not in source or this report.
  The setup helper exports them only to the calling process. Redis uses an
  unused local test port with the application's optional in-memory fallback;
  this is NOT verification of Redis or production rate-limit infrastructure.

## Reproduced defects and changes

1. **Application/schema mismatch:** `Commission.created_at` was mapped in the
   ORM but never created by the real migrations. The real financial regression
   failed with UndefinedColumn during INSERT/RETURNING. Removed this unused
   mapping, retaining the established table and immutable monetary values.
   No historical migration was rewritten and no financial data backfill invented.
2. **Shared test fixture:** two customer actors had the same generated email.
   Added the actor index, preserving real uniqueness constraints.
3. **Logout concurrency fixture:** prefixed 32-character IDs exceeded varchar(36).
   Replaced them with distinct UUID strings; real family-lock interleaving and
   revoked-descendant assertions are unchanged.
4. **Browser harness:** corrected the obsolete "Sign in securely" selector to
   the actual form's "Sign in" button. Blocked external Google font fetches only,
   not application API requests. Serve a freshly built preview rather than the
   development server: traces showed HMR/dev-server interruption and refused
   module requests during cold multi-context navigation. No timeout increases.
5. **New real browser coverage:** session reopening/refresh/expiry/revocation,
   logout replay refusal, CSRF and account separation; shared provider quote,
   admin suitability, customer hold, explicit acceptance, unpaid booking and
   cancellation/capacity release. Vitest explicitly excludes these Playwright
   files; its first run correctly caught the runner-boundary configuration gap.
6. **New test-only helpers:** guarded session expiry/revocation CLI and fictional
   shared prerequisites. Neither is an HTTP production route. Shared fixtures
   reuse the guarded SQL fixtures, pass configurable test passwords over stdin,
   and never contact storage/scanning/payment providers. A seconds-resolution
   fixture pickup is rounded UP to a valid form minute, not before its window.
   Browser cleanup retains the original error if cleanup also fails.

## Execution evidence

- Initial real integration run: **11 failed, 14 passed, 1 skipped**. Failures were
  the commission mismatch, logout-ID fixture, and nine shared-fixture cases.
- Focused rerun after fixes: **12 passed** (financial snapshots, refresh/logout
  concurrency, all nine shared quote/capacity scenarios).
- Real Alembic clean upgrade: **PASS**, base through `20261014_24`, including
  23/24. The isolated migration regression also seeds legacy fictional data
  before 23 and checks re-verification/audit history plus existing booking,
  driver and in-transit trip preservation.
- Offline migration checker: **PASS**, one linear head `20261014_24`.
- Frontend: **46 tests passed**; TypeScript/Vite build **PASS**.
- Ruff (including new Python helpers) and mypy domain check: **PASS**.
- Final combined Chromium run: **6 passed (1.6m)**, zero retries, with the freshly
  built client and real local API/PostgreSQL.
- Final complete backend run:
  `python -m pytest backend/tests -q --tb=short -p no:cacheprovider --cov=app --cov-report=term`:
  **356 passed, 1 skipped, 2 warnings (62.45s); 75% line coverage**. This includes
  **25 passing real PostgreSQL integration cases**, including session persistence,
  financial snapshots, KYC serialization, migrations, shared-capacity transactions,
  phone ownership, rejected-attempt persistence and assigned-driver trip OTP flow.
- The one skip is the separately opt-in legacy
  `test_pilot_auth_database.py` (`PILOT_E2E_DATABASE` unset). This is not a failed
  connection or a skipped requested session/capacity/financial/migration case.
  It was not claimed as executed. Two dependency/config deprecation warnings:
  Starlette's AnyIO BlockingPortal alias and Alembic's legacy path separator.
- Final `git diff --check`: clean (Git emits existing LF/CRLF conversion notices).

Earlier browser runs failed on the obsolete selector, cold dev-server navigation,
runner configuration, and new shared-test selection/date fixtures. They are not
reported as application failures or hidden by retries/skipped assertions.

### What these journeys actually cover

- Real browser → React API client → authentication/roles → FastAPI → PostgreSQL.
- Provider KYC submission, missing-required-document refusal, pending-scan
  refusal, protected versioned access, admin prerequisites/approval, rejection,
  replacement/resubmission history and cross-provider authorization.
- Persistent finite HttpOnly cookie, reopening using persisted browser state,
  invalid-access-token refresh, expired/revoked session refusal, logout cookie
  removal and server replay refusal; independent admin/provider contexts.
- Provider creates the shared quote through the UI; admin records suitability
  through the UI; customer explicitly accepts that revision after a temporary
  hold. Stored amount is INR750 and status remains advance_pending, not paid.
- Customer cancellation currently has no UI control in this journey; its real
  protected API is exercised twice, asserting one release and a duplicate conflict.
- The shared browser scenario seeds route/request/verified identity/vehicle
  prerequisites. It does NOT prove route publication, customer request creation
  or actual identity approval end to end through their UIs. The nine PostgreSQL
  scenarios independently exercise duplicate acceptance, competing acceptances,
  competing holds, conversion/cancellation, expired/superseded quotes, ownership,
  expiry-vs-acceptance and cancellation-vs-expiry races.

### Explicitly simulated or unverified

- S3/GuardDuty in browser KYC: existing test-only fake adapter and explicit
  simulated clean results ONLY on the isolated local database. These results
  do not verify AWS, scanner operation or real identity authenticity.
- MSG91/email in local support app: fake delivery adapters. No real messages.
- Shared SQL fixtures' accepted vehicle documents/verified identities are
  fictional prerequisites, not real scan or review evidence.
- No Razorpay payment/refund or deployed configuration operation was performed.
- Chromium desktop only in this run; full multi-role mobile, publication/request
  UI coverage, real/sandbox integration reconciliation, alerts, restoration and
  independent legal/security review remain release gates.
- **Real KYC approval remains blocked until an approved functioning scanner is
  verified.** Missing/nonclean scan enforcement was not disabled or bypassed.

## Exact PowerShell rerun (this machine/current Windows user)

The ignored helper securely reads the DPAPI-encrypted restricted local credential
and validates the target before exporting application/migration variables. It is
local operational state, not a file to commit or copy to deployment.

```powershell
cd 'C:\Users\harsh\OneDrive\Desktop\english learning\logistic\trucksetu'
docker version
docker start transivox-e2e-postgres
. .\.tmp\local-postgres-env.ps1
& $env:E2E_PYTHON -m pytest backend/tests/integration -q --tb=short -p no:cacheprovider
if ($LASTEXITCODE -ne 0) { throw 'PostgreSQL regressions failed' }
npm run e2e
if ($LASTEXITCODE -ne 0) { throw 'Browser journeys failed' }
npx playwright show-report playwright-report
```

`npm run e2e` resets only the guarded local database and runs real migrations and
seeding; never run it concurrently with database regressions. The test container
and volume are retained for reuse; unrelated containers/volumes were not removed.
If the encrypted helper is unavailable under another Windows identity/machine,
use the masked local URL setup in `2026-10-15-release-candidate-verification.md`.
Never print/recover credentials into chat and never substitute a normal DB URL.

## Next release gate

Review the exact dirty candidate/source manifest and remaining publication/request
UI coverage. Then propose a separately approved isolated staging rollout with
recovery and migration-23 provider re-verification impact. Production and deployed
login behavior were not changed or reverified by this local task. Do not promote
this as public-launch approval: scanning, payment reconciliation, actual delivery,
mobile operations, alerts/restore and independent reviews remain necessary.
