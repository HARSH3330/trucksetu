# TransivoX launch-preparation handoff — 21 October 2026

## Verdict and exact identity

**NO-GO for public launch or candidate deployment yet.** Local code and release
preparation progressed; fresh database journeys, scanner, sandbox reconciliation,
restoration, deployed mobile verification and professional reviews remain gates.
OTP and Google Maps are excluded from this package, not completed.

- Candidate base: `66c63d17897837afc88f457dab0c0e7b8942ac2a`.
- Local branch: `codex/launch-preparation-no-otp-maps`, WITH uncommitted changes.
  HEAD alone is not the tested candidate. See the companion changed-source manifest.
- Production API and frontend source: `ccd594df8a78f56041876c058b522e0624db4fb6`.
- API deployment: `dpl_BycVRnLKUmjYfcKXMbkwrVesGYqj`, project `trucksetu-api`.
- Frontend: `dpl_FExE8Kd4d9uFR29nAgsLHmUUpoB8`, project `trucksetu-whri`.
- Production Neon project `morning-forest-29164100`, branch
  `br-polished-surf-axulzu38` / production, database `neondb`: revision
  `20261014_22`, `users.auth_version` present. Verified branch identity before SQL.
- No commit, push, PR creation, merge, deployment, migration or cloud write.

Review limitation: the requested fresh-context reviewer could not run because
the account returned a usage-limit error. Primary-agent source/diff review was
completed; no independent reviewer approval is claimed. Obtain that review before
merge/release rather than treating the failed dispatch as a pass.

Logout follow-up requested by owner: existing candidate header already exposes
Sign out for any signed-in user, unlike deployed ccd594d. Added phone/desktop
visibility, viewport bounds and 44px target assertions to public-session.spec.ts.
Focused logout/reopen checks: 2 PASS after that test-only addition, with simulated
API. Protected-screen clearing, cookie removal and reload stay covered. No new
application logout implementation or production change was necessary/performed.

The 19 October real PostgreSQL evidence is historical: source manifest
`2026-10-19-postgres-source-manifest.json`, 25 PostgreSQL cases, 6 browser journeys,
356 total backend passes and one separately opt-in skip. It does not establish
that today's payment changes or new browser cases pass against PostgreSQL.

## A. Independent work and actual checks

| Task | Source/changes | Actual result | Boundary/limitation |
|---|---|---|---|
| Late funds preserve trip/booking state | payments.py, test_release_payment_callbacks.py | PASS in backend suite | Real HMAC; fake DB/gateway. No real cancellation/webhook concurrency proof |
| Callback idempotency and malformed events | same | PASS: duplicate/replay, invalid signature, amount/currency/status mismatch, malformed structure | No live webhook or gateway refund |
| Sensitive error logging | middleware.py, test_release_sensitive_logging.py | PASS | Sanitized correlation/type, controlled 500; not an independent audit |
| Recovery/resend/verification | test_account_recovery.py, test_smtp_acceptance.py | PASS | Simulated SMTP acceptance/refusal, expiry/use/attempt/session checks; no mailbox receipt |
| Versioned vehicle scans | test_vehicle_documents.py | PASS | Missing/pending/nonclean registration/download blocked; review/auth/version rules preserved; fake storage |
| Shared publication/request UI | release-shared.spec.ts, fixtures/shared_database.py | COLLECTED + TYPE-CHECKED; execution BLOCKED | Uses UI for route/request, still seeds fictional identities/category/vehicle/driver |
| Mobile vehicle upload/review | release-vehicle.spec.ts | COLLECTED + TYPE-CHECKED; execution BLOCKED | Five marked PDFs, pending scan/refusal, test-only clean, reject/replace, admin review; not real AWS |
| Existing sessions/shared/KYC journeys | existing release-session/kyc specs, integration tests | Historical PostgreSQL PASS; current run BLOCKED | No production/Preview fallback |
| Frontend tooling | package.json/package-lock.json | Vite 8.2.1 -> 8.2.4; source-map-js 1.2.1 -> 1.2.2; fresh npm audit zero | Same-minor security patch, not a broad upgrade |
| Frontend unit/build/browser | npm test; public/design Playwright configs | 46 unit, 37 public and 4 design PASS; builds PASS | Synthetic API/widget boundaries, Chromium; not real integrations |
| Backend checks | pytest excluding integration; Ruff; domain mypy | 353 PASS; lint/type PASS | DB cases explicitly excluded because service unavailable |
| Migrations | check-migrations.ps1 | PASS: one head 24, full offline SQL compilation | Does not prove locks/data migration on today's DB |
| Operations preparation | docs/operations, ops/aws | Prepared only | No policy/monitoring resource applied |

Failures retained: initial backend run 352 PASS / 1 FAIL caused by accumulated
TestClient rate-limit state. The test now owns an isolated limiter dictionary;
limits were not increased or disabled. Final full run: 353 PASS, two existing
dependency warnings. Initial E2E-support collection without E2E_DATABASE_URL
failed closed; unit-mode rerun used no database fallback. Ad-hoc E2E type checking
needed the installed compiler's --ignoreConfig and explicit --types node flags;
the corrected command passed. These were harness/configuration errors, not hidden
application successes.

npm audit initially failed for three launch-editor advisories through Vite:
GHSA-587h-7wmj-h5pm, GHSA-698v-4r3x-3vcv and GHSA-r825-w8mm-5pxw. Patched same-minor
8.2.4 is documented by the upstream advisories; no exploit was run. Both frontend
browser suites were rerun after the dependency change. The main chunk >500 kB
warning remains. Secret-pattern scan flagged two pre-existing fictional test URLs
only (test_neon_config.py, test_phase23_database_safety.py); not a comprehensive audit.

## Connector versus application evidence

| Connector | Read result | What it does NOT establish |
|---|---|---|
| GitHub | PASS, HARSH3330/trucksetu, default main | No write permission test; local changes not published |
| Vercel | PASS, both production aliases and source IDs above | Does not reveal or prove all sensitive runtime bindings |
| Neon | PASS, explicit production branch/schema and aggregate-only impact read | Not local-test access; never used for E2E |
| AWS | BLOCKED: no usable management connector or local boto3 credentials | No current IAM/bucket/scanner/eligibility/cost verification |
| Razorpay | FAIL: filtered test-reference read, Authentication failed / INVALID_ARGUMENT | Not evidence website keys are wrong; no confirmed test/live mode |

Initial GitHub/Neon calls used incorrect parameter names; corrected documented
arguments authenticated successfully. No authorization loop or alternate account.

Production public read-only checks at approximately 03:26 UTC on 21 October:
/health/live 200 alive; /ready 200 database/redis available; /version 200 build ca.
Malformed build identification belongs to the older deployed release; candidate
validation is already implemented but undeployed. No login was attempted. No S3,
scanner, payment, email or session-persistence conclusion follows from readiness.

Production aggregate impact query: zero verified providers, verified applications,
non-rejected legacy KYC documents, bookings, nonterminal trips and approved vehicles.
This is time-bound evidence, not a backfill execution or a promise they remain zero.
Retained recovery/rehearsal branches remain listed and unchanged; they are not
fresh pre-release restore points or proof of historical restoration.

## B. One consolidated owner-action list

| Order | Exact input/approval/action | Why needed / engineering follow-up |
|---|---|---|
| 1 | Repair Docker Desktop Linux-engine health without factory reset/data deletion; confirm engine responds | Current HTTP500 and guarded DB ConnectionTimeout block PostgreSQL, new E2E and restoration. I can then start only the dedicated instance and execute all gates |
| 2 | Restore authenticated read-only AWS management access, or privately inspect standalone S3 Malware Protection eligibility/plan and original error operation/request ID | Determine subscription/account activation versus IAM; no secrets in chat. I will review exact IAM/CORS/scanner diff and regional costs |
| 3 | Review scanner design and approve selected architecture; separately approve any Paid-plan upgrade/resource activation, budget and alert destination | Prefer standalone GuardDuty if eligible. ClamAV worker/table/queue is a proposed new subsystem, NOT implemented/activated. No approval while scanner unavailable |
| 4 | Privately reconnect intended Razorpay TEST merchant; approve isolated staging binding and one specific sandbox payment/refund plan | I verify captured reconciliation, duplicates and refund ledger. Read-only connector cannot itself initiate sandbox payments/refunds |
| 5 | Choose/configure SMTP sender/provider and exact SPF/DKIM records; approve recipient plus one real email send | API-only SMTP_HOST/PORT/USERNAME/PASSWORD/EMAIL_FROM. I test actual receipt, code/reset use and session invalidation afterward |
| 6 | Confirm same-site API domain/cookie deployment topology and DNS ownership; approve domain change separately if needed | Existing www.transivox.in -> *.vercel.app is cross-site; Secure/SameSite=None does not override browser third-party-cookie restrictions. Verify Safari/iOS/private modes before promising browser-reopen persistence |
| 7 | Name primary/backup incident owners, alert channel/recipient, budget, RPO/RTO and log/backup retention | I can configure approved thresholds and run a controlled alert/restoration rehearsal after exact authorization |
| 8 | Supply confirmed registered business/issuer/contact/coverage details and professional decisions for tax, privacy, cancellation/refunds and KYC/Aadhaar retention/consent | I align public policies, consent versions and financial disclosures; cannot invent legal facts or approve legal compliance |
| 9 | Decide Google sign-in, phone-only login, recurring requirements and broader admin configuration scope | Not approved omissions. Existing Google OAuth settings are not a working OAuth flow; recurrence/admin configuration require explicit rules |
| 10 | After local gates/review, approve the exact commit, separate staging resources/tests, then a bounded production migration/API/frontend rollout | No approval to push/merge/deploy inferred here. Real integrations and public launch remain separate approvals |
| 11 | Arrange independent security/penetration and qualified Indian legal/privacy/tax review | Engineering tests do not satisfy these public-launch gates |

No need to send passwords, connection strings, SMS tokens, AWS keys or SMTP secrets
in chat. Use private provider dashboards/masked local prompts. OTP/Maps remain
deferred in this package and are not silently removed from the required product.

## C. Remaining implementation/verification gaps

- BLOCKED: current real PostgreSQL transactions (sessions, financial snapshots,
  payment/cancellation locking, capacity concurrency), migration 23/24 execution,
  eight real-DB browser journeys and local backup/restore. Do not count collection
  or 19 October evidence as a new pass.
- BLOCKED: real scan-clean results, deployed protected provider/vehicle upload,
  renewed manual review and KYC approval. Existing fake scan controls remain local
  test-only. Real S3 probe history is storage evidence, not scanner evidence.
- PREPARED, NOT IMPLEMENTED: ClamAV alternative worker/queue/result store; design
  approval is required before new security subsystem implementation.
- PARTIAL: full customer/provider/driver operational journey through UI, including
  assignment, actual pickup/delivery OTP and payment/invoice transitions. Current
  suites test pieces; no complete current real-DB/mobile journey is claimed.
- NOT IMPLEMENTED: gateway-initiated Razorpay refunds. Existing endpoint records
  an externally completed manual refund; do not represent it as moving money.
- BLOCKED: real email receipt, Razorpay sandbox capture/webhook/refund matching,
  browser-specific deployed cookie restoration, configured alerts and production
  historical restore rehearsal.
- UNRESOLVED: the four product scope decisions above, final policy/retention/
  business financial decisions, independent security/legal review.

## D. Reviewed release proposal — do not execute yet

Proposed coherent commits, not created:
1. Preserve terminal booking state during payment confirmation; lock/idempotency
   and signed-callback regression tests.
2. Redact unexpected runtime errors while retaining secure correlation responses;
   recovery/SMTP and vehicle scan-negative regression coverage.
3. Expand real local shared publication/request and mobile vehicle-review E2E;
   keep test identities/storage controls confined to isolated transivox_e2e.
4. Pin patched Vite tooling/lockfile and include operations/scanner/release docs.

PR description: complete the existing marketplace candidate without changing
provider-quote pricing, payment sequencing, permissions or fail-closed documents.
Attach fresh test outputs and changed-source manifest. Explicitly disclose blocked
DB/scanner/sandbox/restore/mobile gates. Do not merge an unverified dirty snapshot.

After the missing gates pass and the exact source SHA is approved:
1. Verify staging isolation and runtime variables privately. E2E never uses Neon
   production or Preview with unverified database binding. Rehearse bounded
   migrations 22 -> 24 using reviewed source, transaction/timeouts and impact checks.
2. Review production bindings, concurrent release activity and fresh aggregate
   impact. Create/verify a separately approved fresh recovery point before writes.
3. From the approved immutable source, direct MIGRATION_DATABASE_URL,
   `python -m alembic -c alembic.ini upgrade 20261014_24` in backend. This is a
   proposal, not current authorization. Do not run upgrade head blindly.
4. Verify preservation, revision and intended re-verification effects, then deploy
   API from the approved source; check actual cookie/shared routes, version and
   readiness before the matching frontend build. Rebuild VITE_API_URL/config.
5. Verify browser login/roles/reopen/logout, shared quote/hold/accept/cancel/expiry,
   protected versioned documents and actual scanner, reconciled sandbox payments,
   mobile workflows and operational alerts before public promotion approval.

Migration 23 adds provider document pins, marks preexisting verified providers/
applications resubmit_required, rejects unbound legacy documents and appends
audit/reason history. It preserves old evidence, bookings and assignments; it is
not metadata-only. Migration 24 adds route-bound requests/quotes, quote validity/
breakdown/revision snapshots and unique booking acceptance keys. DDL takes locks;
offline compilation does not establish lock duration on production. Both
downgrades intentionally refuse destructive rollback. Do not automatically stamp,
downgrade or restore production: older code can reopen unsafe unversioned behavior.
Use a reviewed security-preserving forward fix; recovery traffic/data-loss impact
requires an explicit decision. Never restore a production copy merely because
an application deployment failed.

New pending changes require no additional migrations beyond the existing 23/24.
Existing cookie configuration: AUTH_COOKIE_SAMESITE, explicit ALLOWED_ORIGINS,
TRUSTED_HOSTS, APP_ENV, SECRET_KEY and finite access/refresh expiry. Secure cookies
in production, server-side origin/custom-header CSRF and finite family revocation
must remain. No new secret variable is introduced by today's fixes.

## Safe rerun on this Windows account

After Docker engine repair (commands below are LOCAL ONLY):

```powershell
cd 'C:\Users\harsh\OneDrive\Desktop\english learning\logistic\trucksetu'
docker version
if ($LASTEXITCODE -ne 0) { throw 'Stop: Docker engine is unavailable' }
docker ps -a --filter name=transivox-e2e-postgres
docker start transivox-e2e-postgres
if ($LASTEXITCODE -ne 0) { throw 'Stop: dedicated container did not start' }
. .\.tmp\local-postgres-env.ps1
& $env:E2E_PYTHON .tmp/check-local-postgres.py
if ($LASTEXITCODE -ne 0) { throw 'Stop: isolated connectivity failed' }
Push-Location backend
try {
  & $env:E2E_PYTHON -m alembic -c alembic.ini upgrade 20261014_24
  if ($LASTEXITCODE -ne 0) { throw 'Stop: LOCAL migrations failed' }
} finally { Pop-Location }
& $env:E2E_PYTHON -m pytest backend/tests/integration -q --tb=short -p no:cacheprovider
if ($LASTEXITCODE -ne 0) { throw 'Stop: PostgreSQL regressions failed' }
npm run e2e
if ($LASTEXITCODE -ne 0) { throw 'Stop: browser journeys failed' }
npx playwright show-report playwright-report
```

The ignored DPAPI helper validates exact transivox_e2e and approved local host
before exporting normal application variables. It must stay private; never copy
it or test credentials to Vercel. npm run e2e resets only that guarded database;
run it sequentially, not alongside other DB tests. If the helper is unavailable,
use the existing masked local setup in the 14/15 October handoff, never a fallback.

Further plans: docs/operations/2026-10-20-storage-scanner-proposal.md,
2026-10-20-payments-email-verification.md, 2026-10-20-alerts-recovery-legal.md,
and the 21 October private-malware-scanner design. All are prepared, not applied.
