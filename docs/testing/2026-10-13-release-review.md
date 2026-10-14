# TransivoX release review — 2026-10-13

## Verdict and scope

The repository is a substantial working foundation, not a verified public-launch product. Local compilation and most isolated tests pass, but the real trip-completion journey, driver access, vehicle files, account delivery/recovery and operations have material gaps. No defensible overall 70–80% figure follows from these results.

Scope is the original attached master requirements, later marketplace-price clarification, AGENTS.md, README, approved admin design and current readiness roadmap. Original requirements include both full-vehicle demand/quotes and shared-capacity supply. Recommending a narrower pilot below is a scope choice for owner approval, not a statement that omitted requirements are complete. Current Vite/React architecture is retained rather than replaced with the originally suggested Next.js stack.

No application code, database, cloud configuration, commit or deployment was changed. Existing dirty work was preserved. Only this report was added; build output and temporary browser screenshot were generated. Temporary diagnostic servers were stopped. No production credentials were printed or live provider calls made.

## Fresh checks and exact boundaries

| Check | Result |
|---|---|
| npm test | PASS: 24 tests, 4 files |
| npm run build | PASS: TypeScript and Vite production build |
| pytest backend/tests --ignore=backend/tests/integration -q -p no:cacheprovider | 177 passed, 1 failed, 2 deprecation warnings |
| Failing test | test_phase19_route_security.py::test_sensitive_routes_reject_anonymous_callers_before_database_access: anonymous PATCH /api/v1/quotes/{id} returns 503, expected 401 |
| Alembic heads / upgrade head --sql | PASS: one head, 20261008_19; offline PostgreSQL SQL compiles; no database migration performed |
| Ruff / mypy | BLOCKED: modules absent in local .venv; not passed |
| Current real PostgreSQL/E2E | BLOCKED: E2E_DATABASE_URL absent; no database fallback/reset attempted |
| Local backend process | Starts; /health/live HTTP 200; /ready HTTP 503 under deliberately nonworking local dependency configuration. Ordinary Windows Uvicorn also reports Psycopg ProactorEventLoop incompatibility. Use existing selector-loop E2E launcher for local database tests; this is not evidence of a Vercel failure. |
| Headless Chromium | Homepage has LIVE MARKETPLACE and hard-coded REQ-1048; sign-in has no forgot-password control; logo leaves capacity screen unchanged while hash becomes #home |
| Mobile sample | Capacity and sign-in at 390x844: no horizontal document overflow; no pageerror observed on capacity navigation. Other screens, keyboard, 360px and authenticated/mobile workflows unverified |
| Browser probe correction | First probe waited for a nonexistent capacity heading and timed out; corrected to actual “Trucks already going your way” and reran successfully. This probe error is not an application defect. |
| Prior owner-supplied KYC result | Three local Chromium scenarios passed before Phase B routing changes. Historical evidence only; fake storage/scans, not real AWS. Current E2E rerun not performed. |
| git diff --check | PASS; existing CRLF normalization warnings only |

Isolated backend tests used APP_ENV=test, empty provider credentials and loopback-only nonworking dependency URLs. Browser used a local frontend pointed to loopback port 9, not the deployed API. Authentication/signup/booking/payment browser journeys therefore were not exercised here.

## A. Progress table

| Feature | Status | Evidence | Remaining work |
|---|---|---|---|
| Frontend build and role-selection helper | Complete and verified at unit/build boundary | 24 tests and production build pass; src/lib/navigation.ts prioritizes API roles | Real login/reload/avatar behavior remains unverified |
| Email/password accounts and refresh | Implemented but unverified end-to-end | auth.py + api.ts + AuthModal + persistent User/RefreshSession | DB journey, delivery/recovery and failure-counter persistence |
| Public recovery / email completion | Missing / partially implemented | No forgot/reset/resend APIs/UI; signup stores verification code but never invokes sender | Single-use recovery, resend, verification UI and configured SMTP delivery |
| Mobile OTP auth / Google OAuth | Missing | Auth API exposes email/password, verification and privileged token operations; config names are not implementation | Implement if required for first launch, or explicitly defer with owner approval |
| Provider KYC | Implemented; historical local simulation verified | KYC API/storage/models + owner-supplied three-test result | Current browser run, actual S3/GuardDuty, admin UI, retention/legal approval |
| Fleet metadata / document-file compliance | Partial / files missing | vehicles.py reviews declared expiry dates; LiveFleet says file uploads deferred; CarrierVehicle lacks file relationships | Vehicle-linked private file/review workflow; approve required document and legacy-vehicle policy |
| Customer requirements, quotes, allocation, consent | Implemented but unverified end-to-end | Wizard -> requests; quote modal -> quotes; comparison -> bookings; server require_terms and acceptance snapshot | Real multi-party DB journey, quote edit/negotiation UI completeness, concurrency/negative paths |
| Driver trip access | Broken by static contract | Phase B routes driver to LiveTrips; it fetches /bookings, which excludes driver role; UI operator also excludes driver | Assigned-driver-scoped list and actions, not global role access |
| Pickup/delivery OTP trip completion | Partially implemented / critical journey incomplete | OTP routes hash/store code but return sent without delivery; LiveTrips only displays waiting, no issue/entry controls | Real delivery adapter/outbox, customer issue and assigned operator verify UI, state/error tests |
| Shared-capacity model | Partial | Search API/UI exists; reservation/booking/match APIs exist; no UI calls to publish/reserve or shared booking; comparison excludes shared allocation | Complete customer/provider journey, or explicitly scope out/disable for pilot |
| Razorpay/offline/refunds | Implemented but unverified | Server-calculated order, captured signature/amount/currency validation, offline admin confirmation and manual refund code | Test-mode checkout/webhook replay/reconciliation + reviewed refund operations |
| Commission/settlement | Partial with confirmed response inconsistency | settlement-eligibility creates immutable Commission but recalculates response from current settings on subsequent calls | Return stored snapshot; approved capture moment, concurrency/idempotency regression |
| Invoices | Partial | Persisted invoice creation/issue and HTML printing exist; no dedicated PDF generation found | Confirm tax semantics with adviser; PDF if original requirement remains mandatory |
| Maps | Partial / external runtime blocked | Google Routes distance/duration/polyline; wizard address fields are plain inputs | Autocomplete/map display/caching absent from inspected path; restricted key setup and actual route operation |
| Chat/trust | Implemented but unverified | Participant-gated conversation APIs, notifications, disputes/cancellation/review APIs and screens | Real participant journey, evidence attachments/operational resolution scope and negative tests |
| Notifications | Partial | External channel classes + NotificationDelivery model exist; no dispatcher calls provider_for; Celery only health/capacity-release tasks | Event delivery outbox/worker, retry/idempotency and preferences; actual sender configuration |
| Admin | Partial | Real overview/KYC/vehicle review links; approved console spec exists; role helper now present | General user/booking lists, privileged role/status mutations and audited operational tabs not implemented |
| Homepage and brand/catalog configuration | Broken live presentation / partial configuration | Constant loads rendered as live; brand and frontend recommendation categories hard-coded; backend catalogue/config exists | Real data/empty states, remove misleading copy; align configurable catalogue/rules |
| Recurring requirements | Missing workflow | Request recurring field alone; no generation/pause/resume scheduler/API found | Implement if retained in launch scope; otherwise explicitly defer |
| Deployment/CI/operations | Partial | Vercel wrapper, production validation, readiness, workflows, logging and local backup script | Workflow repairs, deployed environment checks, monitoring wiring, Neon backup/restore evidence |
| Legal/privacy | Blocked by owner/professional input | Terms marked draft_pending_legal_review; version/hash acceptance exists | Entity/contact details, privacy/refund/KYC consent, retention and qualified review |

## B. Prioritized fixes

Effort: S = focused change, M = multi-file flow, L = schema/workflow/provider implementation; not calendar estimates. C = confirmed from runtime/source; R = high-confidence risk requiring real DB regression.

| Priority | Issue / confidence | Impact | Files/routes | Specific fix | Verification | Effort |
|---|---|---|---|---|---|---|
| P0 | OTP says sent without sending; no trip OTP controls (C) | Real trips cannot complete normal pickup/delivery journey | bookings.py /trips/{id}/otp/*; LiveTrips.tsx; communications.py | Durable authorized delivery with truthful queued/failure states; customer issue and assigned operator verify controls | Harmless local sender adapter + DB OTP journey; staging opt-in actual delivery; no code leakage | L |
| P0 | Driver read/action contract broken (C source) | Driver's default destination fails; cannot operate assigned job | bookings.py my_bookings; LiveTrips.tsx | Return only assigned trips for authenticated driver; enable only authorized actions | Driver A sees own assignments; driver B denied; end-to-end role run | M |
| P0 | Wrong-login/email/OTP counters rolled back on HTTPException (R) | Claimed lockout/attempt ceilings may not persist | auth.py login/verify_email; bookings.py verify_trip_otp; database.py get_db | Prove with separate-transaction read, then persist failure counters atomically before rejection without committing unrelated mutations | Real isolated PostgreSQL repeated wrong attempts/concurrent attempts/expiry | M |
| P1 | Anonymous requests resolve DB before auth (C runtime) | Unauthorized traffic creates DB work; unavailable DB obscures 401 | quotes.py and other db-first signatures; database.py | Establish authentication before DB work on protected routes; audit all dependency graphs | Existing failing route_security test green, DB sentinel must not be called | M |
| P1 | Settlement recalculates returned values despite stored Commission (C source) | Previously recorded payouts and displayed amounts diverge | payments.py /settlement-eligibility | Read existing financial snapshot, transaction-safe creation; retain approved historical rates | Change rates after first snapshot, retry/concurrency assert same values | M |
| P1 | Vehicle approval only reviews metadata (C) | Uploaded per-vehicle evidence cannot be reviewed | models.py CarrierVehicle; vehicles.py; LiveFleet/LiveVehicleReview | Add vehicle-file persistence/migration, clean-scan registration, signed downloads, accepted/unexpired required files and history | Ownership, threats/pending scan, expiry/replacement; legacy data policy before rollout | L |
| P1 | Account recovery/verification delivery missing (C) | Users lose accounts; verification code not delivered | auth.py; AuthModal in main.tsx; communications.py | Secure expiring single-use recovery + resend and email UI/adapter | Enumeration/replay/rate limits/session revocation; staging email delivery | L |
| P1 | Shared-capacity UI incomplete (C) | Original second marketplace model cannot be used normally | LiveCapacity, LiveFleet, LiveQuoteComparison; capacity/matching/bookings APIs | Build publish->match->reserve->consent->book, or explicitly defer and remove false booking CTAs | Weight/volume/route/expiry/concurrency plus real UI journey | L |
| P1 | Full admin console absent (C) | Operators cannot manage required users/bookings from site | LiveAdmin; operations.py; approved admin spec | Add bounded searched/paginated lists and audited mutations within existing permissions | Ordinary admin vs superadmin, self-protection, secret exclusion, suspension revocation | L |
| P1 | New Playwright YAML indentation; general CI lacks dedicated DB settings (C static) | New suite cannot serve as valid release gate | .github/workflows/playwright.yml/ci.yml | Align env indentation; provision exact isolated database/allowed host/flags for relevant job, no fallback | YAML parse, CI and dedicated migration/E2E run | S/M |
| P1 | Public launch configuration/legal/provider verification (unverified external) | Build may deploy but real workflow can fail | .env.example, config.py, DEPLOYMENT.md | Explicit runtime variables + private sender/scanner/webhook setup; finalize policies | Approved staging operation per provider, not just readiness/build | Owner-dependent |
| P2 | Sample loads labelled live and dead logo (C browser) | Misleading availability; navigation failure | main.tsx Home/Logo | API-backed real loads/empty/error or honest demo label; connect logo to view state | Empty DB vs sample fixture; navigate screen->logo->Home at mobile/desktop | S/M |
| P2 | Frontend recommendation hard-coded, partial Maps (C source) | Recommendation/configuration can diverge; address UX incomplete | main.tsx RequestWizard; pricing.py; catalogue | Reuse server catalogue/recommendation and route evidence; preserve advisory fares | Oversized cargo denied; configured category changes reflected; staging route/autocomplete | M |
| P2 | Backup/alerts/document retention incomplete (C code, infrastructure unverified) | Recovery/incident response not demonstrated | backup-postgres.ps1, worker/config, DEPLOYMENT.md | Neon-specific procedure; wired configured error/uptime alerts; reviewed retention/deletion | Approved restore drill + alert exercise + denied private object access | M + owner |
| P3 | Native apps/live GPS/advanced AI/WhatsApp/polish | Not needed for original minimal manual-tracking V1 | Feature flags and roadmap | Keep disabled/deferred; do not imply live GPS or automated payouts | Honest UI/flags; no unfinished clickable promises | Deferred |

No unauthorized data disclosure or real-money loss was reproduced. The failure-counter risk and financial inconsistency require targeted database checks before severity can be fully quantified. Existing Redis rate limiting is a separate control and does not prove the database counters persist.

## C. Fastest completion plan

1. Repair P0 trip/identity invariants and P1 anonymous-auth ordering first. Keep financial use blocked until stored commission response and reconciliation behavior are validated.
2. Complete driver list/action permissions and OTP screens/delivery as one vertical trip journey. Do not substitute an admin manually forcing delivered status or expose production OTPs to make it pass.
3. Fix CI isolation/YAML, remove live demo cards and dead navigation. Preserve Phase B routing and uncommitted KYC work.
4. Add vehicle documents with an additive migration. Owner must settle required documents and treatment of existing approved vehicles. Do not mass-reapprove or revoke production records without approval.
5. Complete account email/recovery, minimal searchable admin users/bookings and operational review actions; finish sandbox payment/webhook/refund reconciliation.
6. Either complete shared-capacity publication/reservation/booking or obtain explicit approval for a full-vehicle-only Delhi pilot. Original requirements are not met by silently dropping Model B.
7. Resume isolated integrated validation, then owner-approved staging operations. Only then review/authorize commit/push and separately approve deployment.

### Smallest safe pilot (requires owner scope approval)

Delhi-area scheduled ordinary packaged-goods full-vehicle requests, provider final quotes, approved multi-provider allocation, private manually reviewed KYC/vehicle files, authenticated assigned-driver manual trips, real OTP delivery, versioned consent, controlled payment/refund and basic admin/support tooling. Optional WhatsApp, GPS, automated KYC/payouts, specialist cargo and sophisticated AI can wait. OAuth/mobile-OTP login, recurrence, PDF invoices and shared capacity cannot be called completed; defer explicitly if not required at pilot launch. The existing manual-distance pricing path must be labelled as manual, not sold as Maps evidence.

### Owner setup (secret values stay in environment settings)

- Frontend: VITE_API_URL points to approved API /api/v1. Public value only.
- API: APP_ENV=production, DEBUG=false, SECRET_KEY >=64 unpredictable characters, explicit HTTPS ALLOWED_ORIGINS and bounded TRUSTED_HOSTS.
- Runtime pooled DATABASE_URL and direct MIGRATION_DATABASE_URL; TLS REDIS_URL and REDIS_REQUIRED=true for operating pilot. Migrations are one-off reviewed release operations.
- AWS_S3_BUCKET, AWS_REGION and least-privilege credentials/role; bucket private, scanner tagging enabled, restricted IAM and reviewed retention. S3 credentials alone do not complete GuardDuty.
- SMTP_HOST/PORT/USERNAME/PASSWORD, EMAIL_FROM and verified sender; MSG91_AUTH_KEY and MSG91_TEMPLATE_ID when ready. AWS_REGION and MSG91_TEMPLATE_ID are supported settings but missing from current .env.example.
- RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET, RAZORPAY_WEBHOOK_SECRET: test mode first; captured webhook and reconciliation evidence before live switch.
- GOOGLE_MAPS_API_KEY with restricted APIs/billing; actual Routes/autocomplete wiring must be separately verified.
- Entity/contact details, commission payer/rate, waiting rules, cancellation/refunds/tax rules; legal/privacy/tax review, monitoring destination, backups and domain approval.

### Local rerun commands

```powershell
# From repository root; use the existing Python 3.12 venv.
npm test
npm run build
& .\.venv\Scripts\python.exe -m pip install -e "backend[dev]"
$env:APP_ENV = 'test'
$env:DEBUG = 'false'
$env:PYTHONPATH = 'backend'
& .\.venv\Scripts\python.exe -m pytest backend/tests --ignore=backend/tests/integration -q -p no:cacheprovider
Push-Location backend
& ..\.venv\Scripts\python.exe -m ruff check app tests migrations
& ..\.venv\Scripts\python.exe -m mypy app/domain.py
& ..\.venv\Scripts\python.exe -m alembic -c alembic.ini heads
& ..\.venv\Scripts\python.exe -m alembic -c alembic.ini upgrade head --sql
Pop-Location
```

Use local-only configuration and blank live provider credentials for ordinary tests. Installing development dependencies requires package access; it was not performed during review.

For KYC database/E2E, privately set E2E_DATABASE_URL to the restricted local user on exact database transivox_e2e, then:

```powershell
$env:APP_ENV = 'test'
$env:TRANSIVOX_E2E = 'true'
$env:E2E_REAL_AWS = 'false'
$env:E2E_ALLOWED_DATABASE_HOSTS = '127.0.0.1' # must match actual approved local host
$env:PYTHONPATH = 'backend'
$env:E2E_PYTHON = (Resolve-Path '.\.venv\Scripts\python.exe').Path
& $env:E2E_PYTHON -m pytest backend/tests/integration/test_kyc_serialization.py -q -p no:cacheprovider
npm run e2e
npx playwright show-report
```

The local E2E command resets the guarded test database. No normal application/Neon fallback is allowed. Existing unrelated pilot-auth integration expects an explicitly disposable database ending _test; it is a different harness and was not run or redirected here.

## Implementation update — 2026-10-14 (local only)

The original audit above is historical. Current release fixes and their evidence:

| Item | Current result | Remaining verification |
|---|---|---|
| Driver access / OTP workflow | Assigned-driver API reused; owner bypass removed; OTP issue/verify controls, acknowledged delivery, state/proof gates, commits and explicit history writes added | Real PostgreSQL multi-role regression, browser trip journey, approved MSG91 delivery/receipt test |
| Failure counters | Targeted commit-before-rejection fixes and locked rows; local request regressions pass | Real isolated PostgreSQL regression blocked: E2E_DATABASE_URL absent. Not claimed proven across actual transactions |
| Anonymous protected routes | AuthenticationFirstRoute rejects missing/invalid bearer before DB dependencies; existing reproduced regression passes | Deployed negative checks |
| Historical commissions | Existing Commission values returned unchanged; new snapshot protected by booking row lock and audited | PostgreSQL concurrency and payment reconciliation |
| CI | Dedicated least-privilege transivox_e2e service/job configured, env indentation fixed; legacy pilot harness kept separate | Workflow parser/execution and isolated DB job still pending |
| Vehicle files | New VehicleDocument table/migration; private direct uploads, signature/size/scan gates, protected downloads, acceptance/rejection history in AuditLog; new approvals require all five existing expiry-rule documents accepted/current/clean | Real DB/browser workflow and S3/GuardDuty. Existing approved metadata-only vehicles are NOT silently revoked; owner-approved backfill/reapproval policy remains a release blocker |
| Accounts | Public recovery/resend/email-code UI and delivery; single-use reset, auth_version access-token invalidation, refresh revocation; password-confirmed trip contact update | Real DB/browser and SMTP delivery. Signup does not automatically dispatch verification email; use Account help to request it. Phone widget is follow-up work |
| Admin minimum operations | Searched/paginated users/bookings; existing trip/payment/invoice/trust/review screens linked; ordinary-account status changes audit/revoke sessions and disable supply | Full admin console remains partial. Reactivation does NOT restore provider/driver supply automatically; separate explicit review and complete operational lifecycle required |
| Homepage / logo | API-backed public previews, honest dependency failure/empty states; state-based home navigation | Current local Chromium negative/mobile checks pass; real API populated state not browser-tested |
| Shared capacity | Original Model B preserved. Backend publication/match/reservation/shared-booking and release APIs exist; LiveCapacity only searches | Provider publication UI, customer evaluate→reserve→consent→shared booking UI, expired-hold scheduling/deployed worker and real weight/volume/concurrency journey still required. No full-vehicle-only scope was chosen |

Fresh checks before phone-widget implementation: **207 backend non-integration tests passed** (two dependency deprecation warnings); Ruff and domain mypy pass; **34 frontend tests/build passed**; **2 local Chromium public/navigation checks passed**; migration check has one head `20261013_21` and offline SQL compiles. No live migration ran. PostgreSQL/E2E remains blocked, not passed. All external delivery/storage/payment operations remain unverified; local doubles cover only external boundaries. No commit, push, deployment or production mutation.

Two additive migrations are now required before verifying this build against a database: `20261013_20` (session version) and `20261013_21` (vehicle files). Do not deploy incompatible code against the older schema. Staging verification is conditional on isolated DB/migration/CI gates passing first; public-launch acceptance below remains unchecked.

### Final local verification and follow-up — 2026-10-14

MSG91 saved-phone ownership flow is now implemented in Account help → Trip contact. Password/email login remains unchanged. The API, not widget success, validates the opaque proof against MSG91 and the active account's saved phone, hashes consumed proofs, rejects replay, and returns no new session/role. Public widget credentials and private account Authkey are separate environment variables. See `2026-10-14-msg91-widget.md` for exact local/Vercel project placement.

Code review found and regression-tested two vehicle-file defects: mutable-key overwrite could change reviewed bytes, and unconditional storage construction prevented safety rejection/suspension. New vehicle records now pin scan/signature/review/download to S3 VersionId; versioning is required. Safety actions instantiate storage only when acceptance/approval needs it. Reviewer follow-up found these fixes coherent. Provider KYC's older key-only references still need equivalent immutability work; this remains a real-storage launch blocker, not a passing local simulation claim.

Two additional identity regressions were fixed: refresh-family revocation now commits before a replay rejection; privileged password recovery increments access-session version and commits before claiming sessions revoked. Their real transaction/concurrency verification remains incomplete without PostgreSQL.

| Fresh check | Result |
|---|---|
| Backend tests excluding infrastructure-dependent integration directory | **220 passed**, two dependency deprecation warnings |
| Backend statement coverage for that run | 71%; not a product completion percentage or whole-system assurance |
| Frontend tests | **38 passed** |
| TypeScript/Vite production build | PASS |
| Ruff / domain mypy | PASS |
| Local Chromium public/widget UI tests | **6 passed**, including 390px phone verification, fallback script, backend denial, explicit-confirmation gate and cancelled callback |
| Workflow YAML parser | All three workflow YAML files parsed; GitHub job execution unverified |
| Migration history/offline SQL | Single head `20261013_21`, offline upgrade compiles; no real database migration |
| Git diff whitespace check | PASS; no commit/push |
| PostgreSQL serialization/counters/trip/phone regressions and full KYC E2E | BLOCKED: no E2E_DATABASE_URL. No fallback/reset attempted |
| Real MSG91/SMTP/S3/GuardDuty/payments/deployed configuration | NOT VERIFIED; no live operations |

Failures encountered and resolved: widget browser fixture initially returned the wrong dashboard shape and lacked the provider overlay stacking (test bugs, corrected without longer timeouts); HTTP 200 without `mobile_verified:true` produced misleading success copy (application bug, now explicitly rejected). Earlier refresh/admin recovery and S3 overwrite/rejection regressions were observed failing before their fixes. Coverage command initially lacked pytest-cov; installing the already-declared dev tooling allowed the successful coverage run. PyYAML was installed as local inspection tooling, not an application dependency. No known failing database-independent check remains in this report; unavailable integration checks are not passed.

Remaining owner decisions: verified-only phone exclusivity versus current all-account claims; existing approved-vehicle backfill/reapproval. Shared-capacity Model B remains required but its customer/provider UI journey is incomplete. No full-vehicle-only scope decision was made. Full admin/supply-reactivation, actual provider runtime, complete multi-role mobile flows, sandbox payment reconciliation, alerts/restore and legal gates remain outstanding. **Not public-launch ready, and staging verification remains gated on the isolated database/migration checks and explicit staging authorization.** Exact PowerShell setup/rerun commands are in `2026-10-14-release-handoff.md`.

### Approved phone-policy follow-up — 2026-10-14

The owner selected exclusivity only after verification. Canonical signup/contact inputs, verified-only ownership checks and a PostgreSQL partial unique index are implemented. Saving the same canonical number retains verification; a different number clears it. Migration `20261014_22` normalizes valid legacy values and refuses invalid/conflicting verified claims; downgrade refuses duplicates rather than deleting or choosing an owner. Suspended verified owners retain ownership. No account receives privileges or sessions from widget verification.

Fresh checks after this change: **225 backend non-integration tests**, **38 frontend unit tests**, **7 local Chromium public/widget tests**, TypeScript/Vite build, Ruff, domain mypy and single-head/offline migration compilation passed. The earlier 71% coverage figure was not refreshed. The new real PostgreSQL concurrent-ownership and rollback-only migration regressions are added but **blocked** by missing `E2E_DATABASE_URL`; no database fallback or live MSG91 call was used. The earlier phone-policy decision gate is resolved; database execution, legacy vehicle decisions and all other unchecked launch gates remain open. Exact guarded commands are updated in the release handoff.

## D. Launch acceptance checklist

- [ ] All anonymous protected calls rejected before DB access; cross-account/role data and mutations denied with no state change.
- [ ] Real local login/reload/refresh/logout/suspension and failure limits proven; verification/recovery delivered with generic responses, expiry/single use and revocation.
- [ ] Provider and each vehicle receive private clean-scanned required documents and explicit manual acceptance; rejected/replaced/expired files cannot satisfy dispatch approval.
- [ ] Customer request -> eligible provider quote -> accepted allocation -> consent -> booking snapshots persist; duplicates/retries/concurrency cannot overallocate.
- [ ] Assigned driver can view only own jobs, receive authorized workflow controls and verify pickup/delivery through delivered; unrelated driver cannot operate them.
- [ ] Customer gets actual OTP via approved delivery channel; wrong/expired/replayed codes and resend/attempt limits persist; no secrets/real identity data in logs.
- [ ] Captured payment/order/amount/currency and webhook signatures verified; duplicates do not double-credit; offline confirmation and refunds audited/reconciled; historical financial values stable.
- [ ] Shared capacity end-to-end passes or owner approves scoped-out pilot with honest disabled UI.
- [ ] Real administrative users/bookings/review/support functions exist with minimized fields, pagination, reasons/audit and protected privilege changes.
- [ ] Legal policies/entity details finalized, consent hash/version evidence recorded and displayed charges match agreed rules.
- [ ] Mobile 360/390/430px core workflows, loading/empty/retry/forbidden states, keyboard labels/focus and navigation pass; no fake live data/dead buttons.
- [ ] CI/lint/type/tests/build and migrations pass; deployed frontend/API origins, readiness and each necessary provider runtime operation pass in approved staging.
- [ ] Backup restoration and alert exercise succeed; private retention/deletion reviewed; independent penetration test and qualified legal/privacy/tax review complete.

Unchecked means unverified or incomplete, not automatically failed. Current review does not approve a public launch.
