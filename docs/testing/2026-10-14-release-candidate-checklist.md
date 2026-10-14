# Release candidate execution checklist — 2026-10-14

Baseline inspected: local `ccd594d`, no tracked changes; generated egg-info preserved.
Working branch: `codex/release-candidate-hardening`. No commit/push/deploy authorization.
This checklist supersedes historical completion claims, not the full audit.

| Item | Owner | Status | Evidence/environment | Exact next action |
|---|---|---|---|---|
| KYC immutable evidence | Codex | verified | Local route regression RED→GREEN: immutable bytes, missing/null versions, wrong-version scan status, legacy refusal | Real PostgreSQL/AWS verification still blocked |
| Legacy provider re-verification | Codex + owner | blocked | Owner explicitly chose re-verification before new operations; migration 23 + authoritative new-driver-operation gates implemented | Test isolated migration rollout before separately authorized production release |
| Logout/session refresh race | Codex | verified | Local client/server-boundary and browser Back/reload regressions pass; shared family transaction lock implemented | Execute new PostgreSQL descendant-refresh/logout interleaving regression |
| Database regressions | Owner + Codex | blocked | E2E_DATABASE_URL absent in current process; no fallback used | Privately configure exact local transivox_e2e URL, validate, migrate, run integration/E2E |
| Complete demand→quotation→booking→trip | Codex | blocked | Real persistence verification needs isolated database; existing trip regression available | Run and extend whole multi-role journey after DB setup |
| Shared capacity publication | Codex | verified | Local provider form sends actual owned vehicle/driver references; API rechecks identity and document eligibility | Real database publication remains unverified |
| Shared capacity evaluation/hold/booking | Codex + owner | blocked | Reservation/booking UI remains incomplete; pricing decision requested (hold amount vs final quotation); DB concurrency unavailable | Owner chooses financial rule, then finish controls and real concurrency/expiry verification |
| Refund/re-review/reactivation/invoice download | Codex | verified | Local refund recording, re-review, driver restoration and printable-record download browser/regression checks pass | Real DB/operator journey, statutory issuer configuration and complete mobile workflow remain unverified |
| MSG91 widget/trip OTP, SMTP, private S3, Razorpay, Maps | Owner + Codex | blocked | Only fake boundaries verified; real calls not authorized | Configure integration table below; authorize staging verification separately |
| Mobile populated journeys | Codex | pending | Public layout regressions exist, not complete real-role evidence | Exercise each completed journey on mobile |
| Alerts and isolated backup restore | Owner + Codex | blocked | No operational target/restore authorization available | Identify isolated restore destination and approve exercise |
| Legal/privacy/refund/retention/entity/coverage | Owner | blocked | Not supplied as approved final content | Obtain qualified review and provide final content |

## Execution decisions

### Confirmed owner decisions — continuation

- Shared capacity is **required**, including publication→search→hold→booking→remaining-capacity updates, concurrency, retry, expiry and cancellation/release. No deferral permitted. The amount relationship between route-rate hold and final quotation is still an unanswered financial rule; a targeted question remains open.
- Persistent login is **required** across browser closure/reopening while the finite session remains valid. Current sessionStorage-only design does not satisfy this. Proposed bounded extension: existing refresh-session model plus persistent HttpOnly refresh cookie, startup role restoration behind a loading gate, origin-protected refresh/logout, existing bearer access authorization. Design approval requested; no browser-readable persistent refresh-token shortcut introduced.
- Metadata-only vehicle approvals must pass private-file review before NEW assignments. Owner reports zero bookings, **not independently verified in production**. No migration/backfill has executed. Existing `pending` state will represent review-required vehicles; read responses additionally show explicit `needs_documents` and missing-file state without rewriting GET data.
- Google sign-in, phone-only login, recurring requirements and broader admin configuration remain unresolved required-scope decisions—not approved deferrals.

### Current continuation status

| Requirement | Owner | Status | Evidence / next action |
|---|---|---|---|
| Vehicle required-file dispatch gates and honest listing | Codex | verified locally | Version-bound accepted files checked through planned trip end; provider explanation and private upload path pass local checks; actual scan/review database journey still blocked |
| Vehicle metadata-approval backfill | Codex + owner | blocked | Repeatable code prepared, production apply disabled. Actual production booking count unknown; configure explicit read-only audit target before any migration/backfill |
| Shared capacity retries and unbooked hold release | Codex | verified locally | Same key requires same body; same match/new key reuses hold; release restores weight/volume once, ownership checked, confirmed booking must use cancellation policy |
| Shared capacity full booking UI / money snapshots | Codex + owner | blocked | Required, not deferred. Hold-versus-final-quotation amount decision remains open; PostgreSQL concurrency/expiry/booking execution blocked by absent E2E URL |
| Persistent login | Codex + owner | blocked | Current sessionStorage does not survive closure. HttpOnly-cookie extension design approval requested; startup/expiry/reopening tests not yet implemented or passed |
| Google/phone-only login, recurrence, broad admin | Codex + owner | pending | No deferral approved. Keep in required-scope backlog; resolve design/scope separately without substituting phone verification for authentication |

Continuation checks: **275 backend non-integration checks passed**, two existing dependency warnings; **42 frontend tests**, TypeScript/build, lint and domain mypy passed. The earlier isolated browser run passed 32 checks, but the latest pre-push full reruns have **31 passed, one startup-timeout failure**; see the limitations below. No real database, production inspection, migration, backfill or live service operation occurred. This is not verification of the full shared-capacity or persistent-login journeys.

### Follow-up security/concurrency review

- Connection-target overrides in URL query parameters could bypass reset/backfill host/database validation. Local and read-only audit tools now allow only explicit non-target connection options; encoded target overrides are rejected. Remote audit URLs additionally require `sslmode=require`, `verify-ca` or `verify-full`. Regression tests observed failure before the fixes, then passed. Production/staging apply remains disabled.
- Expired reservation replay now refreshes identity-map state under the row lock and rechecks terminal state/expiry, preventing stale cached `reserved` state from restoring capacity after confirmation/release. The focused regression observed failure before the fix and passes. Three additional real PostgreSQL interleaving cases are authored/collected but **blocked**, not passed, without `E2E_DATABASE_URL`.
- Assignment, route publication and reservation now lock/refresh the vehicle before checking approval and required files, matching vehicle-before-document review order. A focused suspension regression observed the old path incorrectly assigning, then passed with the locked read. Actual PostgreSQL suspension races remain unverified.
- New reservation acquisition now locates the provider first and locks provider before route, matching booking's parent-first order and removing the reproduced query-order inversion. Focused lock-order regression passes; live PostgreSQL deadlock/race verification remains blocked.

Exact currently read integration variables and actual callback/webhook endpoints: [integration environment map](2026-10-14-integration-environment-map.md). No existing secret values were inspected or printed for that inventory.

### Vehicle-review rollout evidence and exact steps

New dispatch gates require all five accepted immutable-version files to cover the planned trip. The listing distinguishes metadata approval from document eligibility. `backend/vehicle_review_rollout.py` prepares read-only counts and a repeatable **local-only** apply; production/staging apply is disabled.

The production booking count is **blocked** because no explicit approved audit connection is configured here. Do not interpret simulated zero counts or local test data as production evidence. If the real count is nonzero, stop and review affected bookings/trips before eligibility backfill.

```powershell
# READ ONLY against the explicitly approved target, before any release migration/backfill.
# Use a read-only database role. Never paste the URL into chat.
$env:PYTHONPATH='backend'
$auditSecret=Read-Host 'Approved read-only audit database URL' -AsSecureString
$env:VEHICLE_REVIEW_AUDIT_DATABASE_URL=[Net.NetworkCredential]::new('', $auditSecret).Password
$auditSecret=$null
& .\.venv\Scripts\python.exe -m vehicle_review_rollout --environment production `
  --expected-host '<exact approved database hostname>' --expected-database '<exact database name>'
Remove-Item Env:VEHICLE_REVIEW_AUDIT_DATABASE_URL
# Do NOT use --apply for production; it is intentionally rejected.

# LOCAL only, after configuring/validating transivox_e2e and migrating that isolated database:
& .\.venv\Scripts\python.exe -m vehicle_review_rollout --environment local
# Apply only after the actual local report confirms zero bookings and you intend the local change:
& .\.venv\Scripts\python.exe -m vehicle_review_rollout --environment local --apply
```

No vehicle deletion or inferred approval occurs. Candidate status changes preserve previous review metadata and append audit events. Database table locking rechecks zero bookings in the apply transaction; actual PostgreSQL lock behavior still requires isolated verification.

- Work in place on a separate branch to preserve the existing environment and untracked work; no new worktree or dependency install.
- Scope is the supplied execution brief. No shared-capacity deferral or narrowed launch was approved.
- Legacy versions cannot safely be guessed from today's latest object. Owner approved re-verification; migration keeps documents/history and requires new files. No production data has been changed.
- Migration 23 downgrade intentionally refuses to remove evidence pins. Older API rollback must not re-enable unbound downloads/reviews; use a security-preserving forward fix.
- Logout revokes this browser's refresh family, not every device. Already issued access JWTs retain their configured validity (default 30 minutes); client credentials are removed immediately. Network failure is disclosed, not claimed as server revocation success.
- Read-only review found four significant defects: stale refresh clearing new login; descendant-refresh/logout race; legacy linked driver eligibility; refund limit hiding older unpaid records. Fixed locally with generation recheck, shared family lock, authoritative identity gates, and SQL balance filtering before bounded pagination. Real locking and >100-record regression files are authored but blocked, not passed.
- Provider suspended→resubmit is allowed, not direct suspended→verified. Existing rejection terminal behavior is preserved. New driver operations require authoritative identity verification; existing in-flight trip actions are not subjected to the rollout gate.
- Invoice download is an escaped, script-free printable HTML record using stored amounts. Browser Print→Save as PDF is available; a server-generated statutory PDF invoice is not implemented or legally approved. No issuer/GSTIN invented.

## Earlier-batch verification and limitations

The continuation totals above supersede the earlier-batch counts below. Pre-push checks on 14 October: 275 non-integration backend tests, 42 frontend tests, build, lint, domain typing and offline migration compilation passed; 15 guarded database cases collected but not executed. Two public browser-suite runs had 31 passes and one 30-second startup timeout in the vehicle-document explanation test; the unchanged focused rerun passed in 29.5 seconds. The final full-run failure occurs at `page.goto('/#fleet')`, waiting for `load`. Trace confirms slow local module/page startup, but the precise blocking resource/root cause remains unresolved; do not claim a clean browser gate or an application fix. No timeout increase, skipped assertion or authentication bypass was used. This reliability investigation remains engineering work.

Publication is to `codex/release-candidate-hardening`, not a production/main promotion. Migration 23 and provider re-verification require the documented backup/impact checks and explicit release authorization. Production booking count and vehicle backfill remain unverified/unexecuted.

- Backend non-integration: **250 passed** on the final rerun after the logout audit addition, two existing dependency deprecation warnings. Final logout focused checks: two passed.
- Frontend unit: 42 passed. TypeScript/Vite build passed.
- Browser combined suite: **31 passed (1.1m)** after security fixes. Synthetic API/widget boundaries only, not real DB/auth/scanning/payment delivery.
- Ruff and domain mypy passed; migration script passed single head/offline SQL through 23. No migration executed.
- `e2e_database validate` refused exactly: `E2E_DATABASE_URL is required; no application database fallback is allowed`. Integration suite and `npm run e2e` were not run.
- New PostgreSQL files: `test_financial_snapshots.py` (persistent historical snapshots and 100-settled/one-unpaid refund dataset), `test_refresh_logout_concurrency.py` (independent connection interleaving). Authored, unverified. Existing real KYC/counter/phone tests remain blocked.
- All **12 integration cases collected successfully**; collection proves importability only, not test execution or database correctness.
- An intermediate full backend run had one failure because the migration-head contract still expected 22; updated to head 23 with count 23, then combined suite passed. All new implementation regressions were observed failing before their fixes (new driver helper initially failed import because absent).
- Real staging integrations verified: **none**. Explicitly deferred by owner: **none**. Legal/entity/coverage/policy, deployment, alerts, restore and real payment reconciliation remain blocked.
- Fresh-context read-only review completed. Its four significant findings were addressed in one fix pass. Review deliberately did not claim PostgreSQL locking/migration execution, AWS version/IAM/tag integrity, browser execution, gateway reconciliation, deployment, legal invoice validity or restoration. Browser verification was separately executed by the primary agent; all other declined boundaries remain unverified and release-blocking. No optional polish was added as a response to that review.

## Integration setup (values must stay outside Git/chat)

Frontend means the frontend Vercel project / local `.env.local`; API means the separate API Vercel project / local `backend/.env`. Rebuild frontend after changing VITE values.

| Integration | Exact variables / placement | Exposure | Verification, only with approved staging permission |
|---|---|---|---|
| Frontend API boundary | `VITE_API_URL` frontend, API base ending `/api/v1` | Public | Registration/login and CORS from actual frontend domain |
| MSG91 widget | `VITE_MSG91_WIDGET_ID`, `VITE_MSG91_WIDGET_TOKEN_AUTH` frontend | Public widget-only configuration | Signed-in user saves phone, widget proof verified by backend; cancellation/invalid proof leaves unverified |
| MSG91 backend | `MSG91_WIDGET_ENABLED=true`, `MSG91_AUTH_KEY` API | Flag nonsecret, Authkey secret | Backend verifyAccessToken acceptance, ownership/replay/phone binding; never use widget token as account Authkey |
| Trip OTP | `MSG91_AUTH_KEY`, `MSG91_TEMPLATE_ID`, `MSG91_OTP_VARIABLE` API | Authkey secret, template metadata nonsecret | Approved DLT/template variable; issue at legal trip state, accepted is not confirmed delivery, verify code as assigned driver |
| Account email | `SMTP_HOST`, `SMTP_PORT=587`, `SMTP_USERNAME`, `SMTP_PASSWORD`, `EMAIL_FROM` API | Password secret; sender/host nonsecret | Current adapter uses STARTTLS, not implicit port-465 TLS; verify recovery/resend and old session invalidation |
| Private documents | `AWS_S3_BUCKET`, `AWS_REGION`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY` API (or deployment identity) | Keys secret, bucket/region metadata nonsecret | Public access blocked, encryption and versioning, least privilege version read/tag permissions; scanner alone writes exact-version GuardDutyMalwareScanStatus=NO_THREATS_FOUND; signed bytes match uploaded version |
| Razorpay sandbox | `RAZORPAY_KEY_ID`, `RAZORPAY_KEY_SECRET`, `RAZORPAY_WEBHOOK_SECRET` API | Key ID public via order response; both secrets private | Test checkout only; captured webhook signature/order/amount/currency, duplicates and ledger/refund reconciliation |
| PostgreSQL | `DATABASE_URL` pooled runtime; `MIGRATION_DATABASE_URL` direct migration, API/controlled workflow | Both secret | One controlled migration to head, readiness + actual persisted journeys; no startup migrations |
| Redis | `REDIS_URL` TLS `rediss://`, `REDIS_REQUIRED=true` API for operational release | URL secret | Readiness plus actual rate-limit enforcement, not liveness only |
| Maps | `GOOGLE_MAPS_API_KEY` API | Secret server key | Current pricing uses server Routes; restrict APIs/boundary and check real route evidence; do not invent a frontend-key variable |
| App boundary | `APP_ENV=production`, `DEBUG=false`, `SECRET_KEY`, `ALLOWED_ORIGINS`, `TRUSTED_HOSTS` API | SECRET_KEY secret | Explicit domains, correct host/CORS responses, /version and readiness; never copy test secrets |

Widget verification is not login authentication and not booking pickup/delivery authorization. Existing email/password login remains separate. Optional WhatsApp/AI are not required to pretend these three identity operations work.

## Isolated database rerun — PowerShell

If the previously approved local database exists, reuse it; no new Neon/service needed. PostgreSQL/restricted-role setup is in `2026-10-14-release-handoff.md`. Never use the normal application URL as a fallback.

```powershell
cd 'C:\Users\harsh\OneDrive\Desktop\english learning\logistic\trucksetu'
$env:APP_ENV='test'
$env:TRANSIVOX_E2E='true'
$env:E2E_REAL_AWS='false'
$env:E2E_ALLOWED_DATABASE_HOSTS='127.0.0.1'
$env:E2E_CONTROL_TOKEN='local-only-regression-control'
$env:SECRET_KEY='local-only-never-production-0123456789012345678901234567890123456789'
$env:PYTHONPATH='backend'
$env:E2E_PYTHON=(Resolve-Path '.\.venv\Scripts\python.exe').Path
$taskDbSecret=Read-Host 'Restricted LOCAL transivox_e2e URL' -AsSecureString
$env:E2E_DATABASE_URL=[Net.NetworkCredential]::new('', $taskDbSecret).Password
$taskDbSecret=$null
& $env:E2E_PYTHON -m e2e_database validate
if($LASTEXITCODE -ne 0){throw 'Safety validation failed; stop.'}
$env:DATABASE_URL=$env:E2E_DATABASE_URL
$env:MIGRATION_DATABASE_URL=$env:E2E_DATABASE_URL
Push-Location backend
try {
  & $env:E2E_PYTHON -m alembic -c alembic.ini upgrade head
  if($LASTEXITCODE -ne 0){throw 'Isolated migration failed.'}
} finally {Pop-Location}
& $env:E2E_PYTHON -m pytest backend/tests/integration -q -p no:cacheprovider
if($LASTEXITCODE -ne 0){throw 'Database regressions failed.'}
npm run e2e
npx playwright show-report
```

`npm run e2e` resets only the guarded LOCAL test database. Production migration 23 requires a backup/restore point, explicit release authorization and impact review: previously verified providers must re-upload and re-verify. Do not run these test commands against production or staging.

## Release recommendation

**NO-GO for public launch.** Real database journeys, payment reconciliation, real scan/review/delivery, required shared-capacity workflows, legal/security review, deployed configuration, alerts and backup restoration are not proven. No staging integration verified during this work; no functionality explicitly deferred by the owner.
