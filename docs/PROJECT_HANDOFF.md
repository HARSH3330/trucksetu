# TransivoX project handoff

Updated **21 October 2026 (IST)**. Original handoff creation was documentation-only.
Owner subsequently authorized publishing all pending source to this development
branch. Read Git HEAD/status for publication state; the snapshot below identifies
the pre-commit tested contents, not remaining dirty work after publication.
Production rollout remains blocked; no deployment, migration or cloud activation.
**Not public-launch ready.** Read this before continuing; do not restart a broad audit.

## Purpose, architecture and instructions

TransivoX/Trucksetu connects Indian customers with independent transport providers,
fleet owners and drivers. Provider quotations explicitly accepted by customers set
final prices; route-price suggestions are advisory. Shared capacity is required.

React/TypeScript/Vite frontend (`src/`); FastAPI/SQLAlchemy/psycopg backend
(`backend/app/`); PostgreSQL source of truth; Alembic migrations; Redis abuse
protection/coordination; private versioned S3 documents; external-service adapters
in `backend/app/services/`. Frontend/API are separate Vercel projects.

Follow root `AGENTS.md`, `SECURITY.md`, `DEPLOYMENT.md` and `DESIGN.md`, plus any
deeper instructions. Preserve architecture, role/ownership checks, monetary
snapshots and user changes. Use Phosphor-only functional icons. Use applicable
skills: diagnosis/TDD for defects, approved design before new subsystems, fresh
verification before claims. Do not delegate unless active instructions permit it.

## Pre-publication verification snapshot: preserve everything

- Branch: `codex/launch-preparation-no-otp-maps`.
- Base HEAD: `66c63d17897837afc88f457dab0c0e7b8942ac2a`.
- Tests covered this base WITH the following pending changes, not base HEAD alone.
- Modified: `backend/app/api/payments.py`, `backend/app/core/middleware.py`,
  `backend/tests/test_account_recovery.py`, `backend/tests/test_vehicle_documents.py`,
  `docs/testing/2026-10-14-release-candidate-checklist.md`,
  `e2e/fixtures/shared_database.py`, `e2e/public-session.spec.ts`,
  `e2e/release-shared.spec.ts`, `package.json`, `package-lock.json`.
- Untracked: `backend/tests/test_release_payment_callbacks.py`,
  `test_release_sensitive_logging.py`, `test_smtp_acceptance.py` (same directory),
  `e2e/release-vehicle.spec.ts`, `docs/operations/`, `ops/`, the scanner design,
  launch ledger, consolidated handoff/source manifest linked below, and this file.
- Preserve ignored `.tmp/` operational helpers, DPAPI-encrypted local credentials,
  `.venv/`, reports/screenshots and pinned `.tmp/production-schema-ccd594d`
  checkout. Never commit credentials/generated artifacts or reset/clean the tree.
- [Changed-source manifest](testing/2026-10-21-launch-source-manifest.json) records
  19 source/template files; combined SHA256
  `7991604990131366135b7b591845343e9849c106bbeebe166988d601cce7b0b0`.
  Documentation/generated outputs are excluded. Recheck status before editing.

## Last verified production — 21 October

Authenticated Vercel reads identified **both** API and frontend at
`ccd594df8a78f56041876c058b522e0624db4fb6`, branch `main`:

| Resource | Identity |
|---|---|
| Repository | `HARSH3330/trucksetu` |
| API | `trucksetu-api`; `dpl_BycVRnLKUmjYfcKXMbkwrVesGYqj`; https://trucksetu-api-nine.vercel.app |
| Frontend | `trucksetu-whri`; `dpl_FExE8Kd4d9uFR29nAgsLHmUUpoB8`; https://www.transivox.in |
| Neon | project `morning-forest-29164100`; production `br-polished-surf-axulzu38`; endpoint `ep-fragrant-surf-axkjz078`; database `neondb` |

Explicit branch-scoped read-only SQL: revision **20261014_22**, `users.auth_version`
present. Aggregate counts were zero for bookings, nonterminal trips, verified
providers/applications, non-rejected legacy KYC documents and approved vehicles.
These are time-bound observations; recheck before an authorized rollout.

At approximately **03:26 UTC / 08:56 IST**, `/health/live` and `/ready` returned
200; database/Redis available. `/version` returned malformed `ca`; use authenticated
deployment metadata for source identity. Candidate build-ID fix is undeployed.
Runtime DATABASE_URL binding was not independently re-established from secret
configuration. Readiness does not prove S3, scanner, payments or delivery.

Local cookie sessions/logout, shared quote acceptance, provider VersionId
protection and Phosphor/restyle changes are **not deployed**. Current candidate
header has Sign out; deployed source lacks that handler/button.

Retained recovery branches: `pre-migration-20261015` (`br-morning-base-ax0dr2z2`),
`pre-repair-22-20261015` (`br-frosty-mountain-ax2vpqat`); rehearsal
`migration-rehearsal-20261015` (`br-weathered-hill-axdizmg3`). Listed unchanged;
not fresh restore points or proof of historical restoration.

## Completed locally and verification evidence

**21 October**, recorded in the [consolidated report](testing/2026-10-21-launch-preparation-handoff.md):

- Late online/offline payment confirmations preserve cancelled/progressed booking
  states; booking-first locking, webhook replay serialization, malformed-event
  handling and operator audit evidence. Tests use real HMAC but fake DB/gateway.
- Unexpected errors redact exception contents/tracebacks while retaining request
  correlation and controlled secure 500 responses.
- Recovery/email expiry, reuse, attempts, session invalidation and SMTP acceptance
  tests expanded. SMTP is simulated; acceptance is not confirmed mailbox receipt.
- Vehicle nonclean-scan tests expanded; limiter-state test isolation fixed without
  increasing/disabling production limits. Vite patched/pinned to 8.2.4;
  source-map-js lock updated to 1.2.2.
- **353 backend non-integration tests PASS**, Ruff/domain mypy PASS;
  **46 frontend tests PASS**, builds PASS; **37 public + 4 design browser tests
  PASS**, synthetic APIs/widget/storage boundaries, Chromium.
- Final logout follow-up: **2 focused tests PASS**, including 390/1440px visible
  44px logout action, cookie clearing, reload/Back protected-state checks.
- npm audit: zero known vulnerabilities after patch. Offline migration check:
  linear head **20261014_24**, SQL compilation PASS, not database execution.
- Eight real-DB browser scenarios collect; expanded shared/vehicle specs type-check
  but are **BLOCKED, not passed**. They add UI-created route/request and mobile
  vehicle creation/upload/review; fictional identities/compliance prerequisites
  remain seeded. Complete operational/multi-role/mobile coverage remains partial.

[19 October PostgreSQL evidence](testing/2026-10-19-isolated-postgresql-verification.md)
is historical: 25 real PostgreSQL cases, 6 browser journeys, 356 backend passes/
one opt-in skip, including migrations 23/24. Its source fingerprint differs;
do not apply those results to today's pending changes. Fresh-context review
failed immediately on an account usage limit; no reviewer approval is claimed.
Existing bundle-size and dependency deprecation warnings remain.

## Blockers and prioritized remaining work

1. **Restore isolated DB verification:** Docker Linux engine `/v1.56/version`
   returned `500 Internal Server Error`; guarded local connection returned
   `ConnectionTimeout`. Run current DB regressions, eight browser scenarios,
   fix reproduced failures, then isolated backup/restore. No fallback database.
2. **Scanner:** application supports GuardDuty exact-version tags only; ClamAV
   is **not implemented**. No usable AWS management connector/local credentials;
   previous `SubscriptionRequiredException` cause remains unverified. Real
   scanning/deployed KYC are blocked. Historical nine-check S3 probe is storage
   evidence only. Review [scanner design](superpowers/specs/2026-10-21-private-malware-scanner-design.md)
   before new subsystem implementation or paid activation.
3. **Razorpay:** filtered connector read failed `Authentication failed` /
   `INVALID_ARGUMENT`; not evidence website keys are wrong. Reconnect intended
   test merchant, approve isolated sandbox capture/webhook/refund reconciliation.
   Automatic gateway refunds are not implemented; current API records external
   manual refunds.
4. **Release gates:** finish operational/customer/provider/driver journeys,
   real email receipt, deployed browser/mobile persistence (cross-site cookie
   restrictions matter), alerts, backup restoration, independent security and
   qualified Indian legal/privacy/tax review. Resolve business/retention/policy
   inputs; never invent them.
5. **Coordinated release:** fresh recovery/impact review; rehearse bounded
   migrations 22→24, then separately approved production migration, API first,
   matching frontend second. Both migrations refuse destructive downgrade;
   old-code rollback can reopen unsafe unversioned behavior. No automatic restore.

## Non-negotiable decisions and permissions

- Shared capacity is required: provider quote explicitly accepted by customer;
  transactional capacity, expiry/cancellation release, idempotency and immutable
  accepted financial snapshots. Acceptance never means paid.
- OTP/Google Maps are deferred, **not completed**. Google sign-in, phone-only
  login, recurring requirements and broader admin configuration remain unresolved
  scope decisions, not approved omissions.
- KYC registration/review/download require trusted clean status on the **exact
  immutable VersionId**; missing/failed/unsupported/infected remain blocked.
  Clean scanning does not replace manual document acceptance.
- Approved vehicle replacement: admin suspends; admin rejects old document with
  reason; provider uploads replacement; clean scan permits registration; renewed
  document acceptance and vehicle approval. Retain old records/audit history.
- Historical approval covered a specific 18→22 database repair/redeployment;
  it is not authorization for future writes. Current work allows local edits/tests
  and preparation only. No commit/push/merge/deploy, production migrations, cloud
  changes, paid activation, real sends/payments/refunds without specific approval.

## Configuration and local commands

Backend names: `DATABASE_URL` (runtime), `MIGRATION_DATABASE_URL` (direct),
`REDIS_URL`, `REDIS_REQUIRED`, `APP_ENV`, `DEBUG`, `SECRET_KEY`, `ALLOWED_ORIGINS`,
`TRUSTED_HOSTS`, `AUTH_COOKIE_SAMESITE`, `ACCESS_TOKEN_EXPIRE_MINUTES`,
`REFRESH_TOKEN_EXPIRE_DAYS`; frontend public `VITE_API_URL`.
S3: `AWS_S3_BUCKET=transivox-kyc-harsh3330`, `AWS_REGION=ap-south-1`, prefix `kyc/`;
secret names `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY` are backend-only.
SMTP: `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`, `EMAIL_FROM`.
Payments: `RAZORPAY_KEY_ID`, `RAZORPAY_KEY_SECRET`, `RAZORPAY_WEBHOOK_SECRET`;
callback `/api/v1/payments/razorpay/webhook` on the approved isolated API.
Deferred MSG91: public `VITE_MSG91_WIDGET_ID`, `VITE_MSG91_WIDGET_TOKEN_AUTH`;
API `MSG91_WIDGET_ENABLED`, secret `MSG91_AUTH_KEY`, `MSG91_TEMPLATE_ID`,
`MSG91_OTP_VARIABLE`. Deferred Maps: API `GOOGLE_MAPS_API_KEY`.
See `.env.example` and [integration/operations plans](operations/) for
IAM/CORS templates, sender setup and proposed alerts.

Prerequisites: Python 3.12, Node >=22.12, installed project dependencies,
Playwright Chromium, working Docker. If missing: `npm ci`, install backend
editable dev dependencies with venv Python (`-m pip install -e './backend[dev]'`),
and `npx playwright install chromium`.

```powershell
cd 'C:\Users\harsh\OneDrive\Desktop\english learning\logistic\trucksetu'
docker version                         # stop on engine error
docker ps -a --filter name=transivox-e2e-postgres
docker start transivox-e2e-postgres    # existing dedicated instance only
. .\.tmp\local-postgres-env.ps1       # private DPAPI helper; never print/copy
& $env:E2E_PYTHON .tmp/check-local-postgres.py
if ($LASTEXITCODE -ne 0) { throw 'Stop: isolated DB unavailable' }
# LOCAL ONLY; inspect exact target before any migrations/resets:
Push-Location backend
try { & $env:E2E_PYTHON -m alembic upgrade 20261014_24 }
finally { Pop-Location }
if ($LASTEXITCODE -ne 0) { throw 'Stop: local migration failed' }
& $env:E2E_PYTHON -m pytest backend/tests/integration -q -p no:cacheprovider
if ($LASTEXITCODE -ne 0) { throw 'Stop: PostgreSQL tests failed' }
npm run e2e
npx playwright show-report playwright-report
```

Container/volume: `transivox-e2e-postgres` / `transivox_e2e_postgres_data`;
loopback port 55432, restricted `transivox_e2e_user`. Require explicit
`E2E_DATABASE_URL`, exact `transivox_e2e`, approved local host,
`APP_ENV=test`, `TRANSIVOX_E2E=true`, `E2E_REAL_AWS=false`. Helper validates before
exporting runtime variables. Never use production/Preview/Neon as E2E fallback.
Browser tests reset this isolated DB; run sequentially. Test account defaults:
provider.e2e@example.com/admin.e2e@example.com; credentials configurable, not copied here.

For manual local fake-boundary development after validation, use separate shells:
venv Python with `PYTHONPATH=backend` → `-m e2e_server --port 18000` from backend;
frontend `VITE_API_URL=http://127.0.0.1:18000/api/v1`, `npm run dev` from root.
Do not run manual servers alongside Playwright-managed servers. No real AWS.

## Single next task

**Restore the existing isolated PostgreSQL service and verify this exact dirty
candidate.** Acceptance: engine reachable; dedicated container/volume preserved;
exact-name/host/restricted-role checks pass; local migrations through 24 and
current session/capacity/financial regressions pass; all eight real browser
journeys run or precise failures recorded; source fingerprint updated. External
integrations stay simulated and KYC scanner approval stays blocked. Stop on
unsafe targets; request approval before disruptive Docker recovery. Use the
consolidated report for details, not a new broad audit.
