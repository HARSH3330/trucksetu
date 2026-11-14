# TransivoX functionality audit — 2026-10-14

## Release candidate continuation — local changes, not deployed

See `2026-10-14-release-candidate-checklist.md` for the single current owner/status/evidence/action ledger and exact integration/setup commands. This continuation implemented provider-KYC version pinning and owner-approved legacy re-verification (migration 23), visible logout with session-family serialization/client race handling, new-operation provider/driver eligibility gates, admin manual refund recording/pagination/retry validation, escaped stored-value printable invoice records, provider shared-capacity publication and provider/driver re-review controls. No commit, push, deployment, production data change or live provider operation occurred.

Fresh local evidence: 250 backend non-integration checks, 42 frontend tests, 31 synthetic-boundary Chromium tests, build/lint/domain types and single-head/offline migration checks passed. PostgreSQL suite collected 12 cases but execution remains blocked by absent guarded `E2E_DATABASE_URL`; collection is not a pass. No real S3/GuardDuty/MSG91/SMTP/Razorpay integration was verified. Customer shared-capacity evaluation/reservation/booking is incomplete and awaits the explicitly requested hold-versus-final-quote financial rule; no shared-capacity deferral was approved. Printable records are not a legally approved statutory invoice or server-generated PDF. Public launch remains NO-GO.

## Post-audit fix verification — 2026-10-14

The two reproduced sign-in defects documented below are now fixed. Homepage route values are consumed once after draft persistence, so authentication remounts restore edited values. Protected views are keyed by the API-returned user ID and reload after sign-in rather than retaining anonymous state. Both regression tests were freshly observed failing before the fixes, then passed unchanged.

Fresh final checks: **25 browser tests passed (zero failures), 38 frontend tests passed, 225 backend non-integration tests passed**, TypeScript/Vite build, Ruff, domain mypy and single-head/offline migrations through `20261014_22` passed. Static follow-up code review found no new critical/important issues in these edits. The owner explicitly confirmed production migration through `20261014_22` and authorized pushing to main; that confirmation is not independent database verification. No production migration, real SMS/email/payment or AWS operation was performed by the agent.

The remaining feature/integration/security/operational gaps below are still open. Real local PostgreSQL journeys remain blocked by absent `E2E_DATABASE_URL`; no fallback was used. This update supersedes the historical two-failure result and BROKEN booking row below, not the overall not-public-launch-ready verdict. All UI/footer/widget source updates are included in the authorized main rollout; deployment and real OTP delivery must still be verified separately.

## A. Current verdict and evidence boundary

**Not ready for public launch.** The frontend builds and many local request/domain tests pass, but the complete persisted multi-role marketplace journeys have not been verified here. The current browser suite has **23 passes and 2 reproducible application failures**. No application code was changed during this audit; existing unfinished UI/release work was preserved. Only this report was added. No push, deployment, database reset/migration, real message, payment or AWS operation occurred.

Sources: repository AGENTS.md, README, original master requirements attachment, current routes/components/models/adapters, `2026-10-13-release-review.md` including implementation/phone-policy updates, and `2026-10-14-release-handoff.md`. The README's phase-completion and demo-data statements are historical claims, not execution evidence. Current requirements include both demand/quotation bookings and shared capacity; this audit does not silently narrow launch to full vehicles.

Users can exercise the local public navigation, route entry, load search/filter, safety/FAQ/policy-preview pages, and controlled unavailable states. Synthetic browser fixtures also prove specific sign-in/phone/KYC UI behavior. They do **not** prove real account creation, PostgreSQL persistence, scanner operation or message delivery. Previously user-reported passing KYC/database runs are historical and were not substituted for fresh checks.

**Live OTP:** a read-only GET of `https://www.transivox.in/` returned HTTP 200. Its loaded entry JavaScript did not contain either the MSG91 widget-loader URL or `/auth/mobile/verify-widget` integration path. This is evidence that the inspected published frontend entry does not include the new widget integration, not a test of every deployed API/SMS capability. MSG91/widget/template variables were absent from this process and the checked local `.env`, `.env.local`, `backend/.env` configuration sources. Vercel environment settings were not accessible/verified. **Live OTP has not been enabled or verified by this audit.** The latest audit request prohibits deployment and real SMS, superseding the earlier activation request for this turn.

## B. Feature matrix

Statuses refer to the stated scope; passing unit tests never upgrades an entire connected journey to VERIFIED WORKING.

| Feature | Role | Status | Current evidence | Remaining work / priority |
|---|---|---|---|---|
| Public routes, deep links, Back, reload | Public | VERIFIED WORKING — local frontend | Fresh Chromium hash-route tests for loads/capacity, selected load and shipping refresh | Deployed/mobile complete-flow verification; P2 |
| Public load preview/search/filters | Public/provider | VERIFIED WORKING — synthetic API boundary only | Same `/requests` data consumer; filters apply/reset actual fixture rows, selected reference survives reload | Real published DB rows; pagination/expired-load policy; P1/P2 |
| Requirement route/cargo wizard | Customer | PARTIALLY WORKING | Local route handoff, blank defaults, validation, refreshed draft and synthetic publish/reference pass | Real create→list persistence; edited draft overwritten after sign-in; P1 |
| Requirement edit/cancel/recurrence | Customer | MISSING | Requests API exposes create/public list/mine; no edit/cancel or recurrence workflow discovered | Add approved edit lifecycle and daily/weekly/monthly templates/jobs; P1 |
| Email/password registration/login | Public | PARTIALLY WORKING | Auth routes, hashing/validation/lockout code; local form/error tests | Real register→verify→login/reload journey; post-login private-screen defect; P1 |
| Logout/logout-all | All | PARTIALLY WORKING | Backend endpoints and session revocation exist; no active website logout control discovered | Complete UI session termination and reload/revocation tests; P1 |
| Refresh/access session persistence | All | IMPLEMENTED, UNVERIFIED end-to-end | Shared client rotation, persistent sessions/auth_version; unit rejection tests pass | Isolated DB rotation/replay/suspension across requests; P1 |
| Anonymous authentication preflight | Protected endpoints | VERIFIED WORKING — local ASGI/test boundaries | Fresh backend regression suite includes rejection before DB dependency resolution | Deployed negative probes; P1 |
| Roles/resource ownership | All | IMPLEMENTED, UNVERIFIED across real journeys | Server checks; local driver/KYC/admin/security regressions pass | Separate-account DB/browser authorization matrix; P1 |
| Email verification/resend/recovery | All eligible accounts | IMPLEMENTED, UNVERIFIED end-to-end | AccountSecurity, account_recovery, SMTP adapter; fake-boundary tests | Test delivery→reset→new login→old session denial; real SMTP setup; P1 |
| Saved-phone ownership widget | Authenticated users | VERIFIED WORKING — fake widget/provider boundaries only | Success requires backend confirmation; denial/cancel/stale proof/unchanged phone checks pass | Migration 22/concurrent DB proof, deployed settings and approved MSG91 SMS; P1 |
| Phone-only OTP sign-in / Google OAuth | Public | MISSING | Widget verifies a signed-in account; it does not create sessions. No Google OAuth flow discovered | Separate authentication design/implementation; original auth requirements; P1 |
| Customer/provider dashboards | Customer/provider | IMPLEMENTED, UNVERIFIED with real DB | API summaries, roles and navigation; empty synthetic states pass | Actual request/quote/bookings values and persistence; P1 |
| Driver workspace | Driver | IMPLEMENTED, UNVERIFIED end-to-end | Trips destination and `/drivers/me/trips`; active/verified/assignment checks | Real assigned vs unassigned driver journey; P1 |
| Admin overview/users/bookings | Admin/superadmin | PARTIALLY WORKING | Searched/paginated APIs, account suspension audit/session revocation; mobile review navigation passes | Complete operational lifecycle/real records; privileged management intentionally restricted; P1 |
| Provider KYC upload/scan/submit | Provider/owner/driver | IMPLEMENTED, UNVERIFIED with DB/storage in this audit | Create/registered/under_review APIs and fake clean-scan controls; existing suite available | Fresh guarded PostgreSQL KYC run and real storage test; P1 |
| KYC protected access/review/replacement/resubmission | Admin/provider | IMPLEMENTED, UNVERIFIED with DB/storage in this audit | Role-scoped signed access, required acceptance, decision history; backend regression tests pass | Full fresh admin queue→file→decision→provider persisted state; P1 |
| Provider KYC reviewed-byte immutability | Provider/admin | PARTIALLY IMPLEMENTED — security gate | `kyc.py` stores/checks/downloads key-only references; unlike vehicle documents, no recorded VersionId | Bind review and download to immutable bytes; actual overwrite exploit not run; P0 launch gate |
| Vehicle creation/private files/review | Provider/admin | IMPLEMENTED, UNVERIFIED end-to-end | VehicleDocument/migration 21, version-pinned S3 operations, clean gates, UI exists | PostgreSQL+browser+real S3/scan verification; P1 |
| Vehicle editing/availability management | Provider/admin | PARTIALLY WORKING | Registration/list/admin review present; no general vehicle edit workflow discovered | Approved change/re-review lifecycle and operator availability controls; P1 |
| Existing approved vehicle backfill | Provider/admin | BLOCKED — policy decision | Metadata-only approvals were not automatically revoked | Owner-approved required-file/backfill rollout; P1 |
| Drivers creation/linking/editing | Provider/admin | PARTIALLY WORKING | Driver account linkage/create/list exists; editing/complete reactivation workflow not discovered | Full persisted linkage, expiry and supply-reactivation controls; P1 |
| Provider quotation/versions/counter-offers | Provider/customer | PARTIALLY WORKING | POST/PATCH quotes, immutable versions, comparisons/counter offers; actual UI submits quotations | Complete quote-edit/respond UI, real multi-account negotiation; P1 |
| Terms-gated allocation/booking | Customer | IMPLEMENTED, UNVERIFIED end-to-end | TermsConsent and backend require_terms; transactional allocations/snapshots | Customer→provider→accepted booking with real DB and policy evidence; P1 |
| Booking cancellation/reviews/disputes | Participants/admin | IMPLEMENTED, UNVERIFIED end-to-end | Stored cancellation preview, participant access, review/dispute/resolve APIs and UI | Real fee/refund/history and admin resolution; evidence upload remains deferred; P1 |
| Private bookings after sign-in | Customer | BROKEN | Fresh Chromium remains on signed-out state after accepted login at `#bookings` | Remount/refetch on auth change; P1 |
| Trip assignment/transitions/assigned-driver actions | Provider/driver/admin | IMPLEMENTED, UNVERIFIED end-to-end | Eligibility/ownership/state/proof gates and unit request checks | Complete real journey B/C; P1 |
| Pickup/delivery OTP issue/resend/expiry/attempts | Customer/driver/admin | IMPLEMENTED, UNVERIFIED end-to-end | Hashed independent codes, commits/locks, send acknowledgement required, accepted≠delivered response | Persisted limits/concurrency and real template acceptance/delivery; P1 |
| Razorpay test checkout/captured webhook | Customer/system | IMPLEMENTED, UNVERIFIED sandbox | Server orders, signature/captured amount/currency checks, event idempotency; UI explicitly test-key only | Sandbox payment→verified webhook→booking/ledger reconciliation; live-key UI not enabled; P1 |
| Offline payment/manual refunds | Customer/admin | PARTIALLY WORKING | Pending confirmation, admin confirmation and manual-refund APIs/audits exist | Complete operator refund UI/workflow, retries and persisted reconciliation; P1 |
| Commission/settlement history | Admin | IMPLEMENTED, UNVERIFIED with DB | Stored snapshot response regression passes; row lock snapshot creation | Config-change/concurrent-request DB regressions + reconciliation; P1 |
| Invoice draft/issuance | Customer/admin | PARTIALLY WORKING | Models, APIs, draft/issue UI exist | Actual billing/tax review and PDF/download/export workflow absent; P1 |
| Shared capacity search | Public/customer | IMPLEMENTED, UNVERIFIED search journey | Search page/navigation renders in local browser; matching APIs exist. No complete search submission against real DB executed | Actual search/result matching, route/capacity data and journey; P1 |
| Shared publish→evaluate→reserve→book→release | Provider/customer | PARTIALLY IMPLEMENTED | Backend publication, locked weight/volume holds, match/consent/booking APIs exist; UI searches only | Provider publication + customer reservation/consent/booking UI, expiry worker and concurrent DB test; P1 |
| Notifications/preferences/chat | Participants | IMPLEMENTED, UNVERIFIED end-to-end | Booking-scoped participants/messages and in-app delivery models/APIs/UI | Cross-user DB/privacy/delivery/read tracking; real workers/providers; P1 |
| Public safety/FAQ/support/footer | Public | VERIFIED WORKING — local frontend | Signed-out support/Terms fixture, configured public email/hours, responsive footer | Actual support operations/registered entity/coverage confirmation; P1 launch content |
| Privacy and standalone refund policies | All | MISSING | Current pages explicitly say separate policies are not published | Qualified policy review and publish/version/acceptance consistency; P1 |
| Maps/advisory pricing | Public/customer | IMPLEMENTED, UNVERIFIED real service | Controlled missing-key error and manual-distance path; Google Routes adapter exists | Restricted key/runtime route check; UI exact claim alignment; P1 |
| AI extraction/recommendation/risk | Customer/admin | PARTIALLY WORKING | Optional backend adapters/domain rules; text-assisted wizard correctly unavailable | Connect approved extraction/risk review UI or explicitly defer; P2 |
| Admin catalogue/settings/flags/reporting | Admin | PARTIALLY WORKING | Settings/catalogue models, env flags, audit/analytics exist | Operational configuration UI and real data reports; P1/P2 |
| CI/migrations/deployment/alerts/backups | Operators | IMPLEMENTED, UNVERIFIED operationally | YAML parses, single head/offline SQL; workflows/scripts/log hooks exist | Actual isolated CI, migrations, deployed config, alert exercise/restore; P1 |
| Mobile essential multi-role journeys | All | PARTIALLY WORKING | Public/sign-in layouts at 360/768/1280, mobile fake admin/provider checks pass | Populated Fleet/trips/payments and real auth/keyboard journeys; P1 |
| Native apps/GPS hardware/international logistics/advanced ML/FASTag | Future roles | OUT OF SCOPE for V1 | Original requirements explicitly defer these/future capabilities | Do not treat them as current launch defects |

## C. Reproduced defects and separate risks

### 1. Edited shipping destination is overwritten after login — P1

- Reproduce: Home pickup Pune/drop Mumbai → Get transport quotes → edit destination to Delhi → fill harmless cargo and review → Publish while signed out → Sign in to publish → successful fake login.
- Expected: Delhi remains the authoritative saved draft. Actual: destination becomes Mumbai.
- Files: `src/main.tsx` App shipping/sign-in branch and RequestWizard initializer; `e2e/public-followup.spec.ts:73`.
- Cause: authentication unmounts the wizard; remount reapplies original routeSeed over saved edited draft.
- Fix: consume/clear the seed once or retain the authoritative draft across auth. Acceptance: existing regression passes without dropping assertions; persisted edits survive cancel/login/refresh and no duplicate publication.

### 2. Bookings remains signed out after successful login — P1

- Reproduce: `/#bookings` anonymously → Sign in → successful fake customer login.
- Expected: current route refreshes authenticated bookings/empty state. Actual: “Sign in to view bookings” remains.
- Files: `src/main.tsx` AuthModal completion and LiveBookings mount-only loader; `e2e/public-followup.spec.ts:98`.
- Cause: route is preserved, but its loader does not react to the changed authenticated user/session.
- Fix: refetch/remount protected views on auth identity changes, preserving intended public/ship destinations. Acceptance: current regression reaches “No bookings yet” and real DB records subsequently refresh correctly.
- Related private-support behavior is a **suspected same-pattern risk**, not an independently executed failing journey in this audit.

### Static gaps/risks — not reproduced breaches

- Provider KYC references are not immutable-version pinned. Vehicle files have the newer protection. Treat as a security release gate, not a claim that AWS overwrite exploitation was demonstrated.
- Public `/requests` has no pagination cap or pickup-date expiry filter in its inspected query. Browser filters operate on loaded rows. Agree expiry/archive behavior and cap/paginate before larger-scale usage; no load/DoS test executed.
- Required recurring jobs, Google OAuth/phone-only login, invoice download and several edit/configuration workflows were not discovered. Marked missing/partial above, not hidden to obtain a passing report.
- Currency frontend rendering uses Number in places; backend is still amount authority. Financial reconciliation/concurrency remains unverified, not proven safe by display calculations.

## D. External setup and OTP activation boundary

| Integration | Code readiness | Local verification | Real-service verification | Required setup |
|---|---|---|---|---|
| PostgreSQL | Models + migrations through 22 | Offline SQL/guard tests pass | BLOCKED: no E2E_DATABASE_URL | Restricted user, exact local transivox_e2e; no fallback |
| Redis | Rate limits/readiness/adapters exist | Fake boundaries/unit checks | Not verified now | TLS Redis URL and runtime/limit tests |
| MSG91 widget | React loader + backend verifyAccessToken + proof binding/replay guards | Fake widget/HTTP tests pass | Not live-verified; inspected public bundle lacks integration signatures | Frontend VITE_MSG91_WIDGET_ID and VITE_MSG91_WIDGET_TOKEN_AUTH; API MSG91_WIDGET_ENABLED=true and private MSG91_AUTH_KEY; approved rollout after DB gates |
| MSG91 trip OTP | Separate template sender, accepted/unconfirmed status | Fake delivery contracts/OTP tests pass | No real SMS sent | API MSG91_AUTH_KEY, approved MSG91_TEMPLATE_ID and MSG91_OTP_VARIABLE/DLT; acceptance and receipt tests |
| SMTP/account email | Resend/recovery sender + UI | Fake-boundary tests pass | No real email sent | SMTP_HOST/PORT/credentials, EMAIL_FROM, verified sender/TLS |
| S3/GuardDuty | Private signing and scan gates; vehicles version pinned | Fake storage tests pass | No real uploads/scans | Private encrypted/versioned bucket, least privilege and scanner-only clean tags; provider KYC version fix |
| Razorpay | Test-key checkout, orders/captured webhooks/refunds | Backend unit/fake checks | No sandbox/live payment executed | Test API keys + separate webhook secret; reconcile before live rollout |
| Maps | Google Routes + honest missing-config path | Adapter/domain tests | Not called | Restricted server/browser keys at correct boundary; approved runtime test |
| WhatsApp/Gemini | Optional adapters/flags | Limited fake/domain evidence | Not called/enabled | Deliberate optional setup; not necessary to fake launch completion |

Environment presence checks did not print credentials. Setting a variable or a green build is not proof of provider connection. Widget tokenAuth is frontend-public widget configuration, **not** the private account Authkey. Widget ownership verification is **not phone-only login** and does not verify provider KYC. Trip OTP and widget verification are separate integrations.

## E. Fastest completion backlog

1. **P1/S — implementation:** fix the two reproduced auth/route state defects; rerun all browser tests. Complete website logout and cross-session refresh states.
2. **P1/S configuration + M verification:** configure isolated local PostgreSQL; run migrations 20–22 and real counter/phone/KYC regressions. Do not deploy unverified schema changes.
3. **P0/M — implementation + verification:** pin provider-KYC reviewed bytes, settle legacy vehicle backfill; prove protected file access/scan/required acceptance in DB and approved storage sandbox.
4. **P1/L — connected journey:** demand→quote/edit/negotiation→Terms/allocation→vehicle/driver→trip/OTP, including role denials, retries, expired/wrong proofs and state agreement.
5. **P1/M — external delivery:** privately configure SMTP/MSG91; approve staging rollout/SMS separately; validate server proof and trip acceptance/receipts. Do not grant verification from browser success alone.
6. **P1/L — financial verification:** sandbox captured webhook/payment/order mismatch/replay/offline/refund/invoice/commission reconciliation and stored historical snapshots; complete minimum operator refund actions.
7. **P1/L — implementation:** complete shared-capacity publication/evaluation/reservation/consent/booking/expiry release UI and concurrency tests. No full-vehicle-only scope reduction was approved.
8. **P1/M–L — requirements decisions/implementation:** recurring jobs, Google OAuth/phone-only sign-in, request/vehicle editing, invoice download and complete admin settings. Obtain explicit scope decisions if deferring required features.
9. **P1/M — operational/legal verification:** finalized legal/privacy/refund/registered entity/coverage, mobile populated workflows, CI/deployed configuration, alerts, backup restoration and independent security review.

## F. Fresh test results and commands

| Command | Result |
|---|---|
| `.venv\Scripts\python.exe -m pytest backend/tests --ignore=backend/tests/integration -q -p no:cacheprovider` | **225 passed**, 2 dependency deprecation warnings |
| `.venv\Scripts\python.exe -m ruff check backend/app backend/tests backend/migrations --config backend/pyproject.toml` | PASS |
| `.venv\Scripts\python.exe -m mypy backend/app/domain.py` | PASS — domain file only |
| `scripts/check-migrations.ps1` with venv Python on PATH | PASS single head 20261014_22 / offline SQL only; no DB migration |
| Parse `.github/workflows/*.yml` with PyYAML | 3 parsed; CI jobs not executed |
| `npm test` | **38 passed** |
| `npm run build` | PASS TypeScript/Vite |
| `npx playwright test --config playwright.public.config.ts` | **23 passed, 2 failed**, no skipped tests; failures above |
| Real PostgreSQL/full `npm run e2e` | **BLOCKED**, not executed; no configured safe DB |
| Journeys A–F against real local DB | **BLOCKED**, none completed in this audit |

Ordinary tests used APP_ENV=test, TRANSIVOX_E2E=true, E2E_REAL_AWS=false, a synthetic test secret and an unreachable local dummy runtime DB URL to prevent accidental production access. This dummy was **not** an E2E_DATABASE_URL fallback. MSG91 was disabled for the test process. No live delivery provider was contacted.

Browser evidence: `playwright-public-report/index.html`; failure screenshots and retained traces under `test-results/public/public-followup-edited-shi-9aa05-everting-to-homepage-values/` and `public-followup-successful-53745-ent-private-bookings-screen/`. Public/mobile screenshots under `test-results/ui-after-home-1280.png` and `ui-followup-mobile.png`. Safe synthetic records only. No frontend lint command/config is supplied; no lint success is claimed. Build success does not conceal the browser failures.

### Exact Windows setup/rerun

If no isolated PostgreSQL server exists, follow the optional Docker/restricted-role setup in `2026-10-14-release-handoff.md` (new local server only; do not run PUBLIC revocations on a shared server). Existing approved test databases should be reused, not recreated. The runtime role must be limited to transivox_e2e, not a Neon/shared administrator.

```powershell
cd 'C:\Users\harsh\OneDrive\Desktop\english learning\logistic\trucksetu'
$env:APP_ENV='test'
$env:TRANSIVOX_E2E='true'
$env:E2E_REAL_AWS='false'
$env:E2E_ALLOWED_DATABASE_HOSTS='127.0.0.1'
$env:E2E_CONTROL_TOKEN='local-only-audit-control'
$env:SECRET_KEY='local-audit-only-never-production-01234567890123456789012345678901234'
$env:PYTHONPATH='backend'
$env:E2E_PYTHON=(Resolve-Path '.\.venv\Scripts\python.exe').Path
$taskDatabaseSecret=Read-Host 'Restricted LOCAL transivox_e2e URL (never paste into chat)' -AsSecureString
$env:E2E_DATABASE_URL=[Net.NetworkCredential]::new('', $taskDatabaseSecret).Password
$taskDatabaseSecret=$null
& $env:E2E_PYTHON -m e2e_database validate
if($LASTEXITCODE -ne 0){throw 'Safety checks failed; do not migrate/reset.'}
$env:DATABASE_URL=$env:E2E_DATABASE_URL
$env:MIGRATION_DATABASE_URL=$env:E2E_DATABASE_URL
Push-Location backend
try {
  & $env:E2E_PYTHON -m alembic -c alembic.ini upgrade head
  if($LASTEXITCODE -ne 0){throw 'Isolated migration failed.'}
} finally {Pop-Location}
& $env:E2E_PYTHON -m pytest backend/tests/integration/test_kyc_serialization.py backend/tests/integration/test_release_counter_persistence.py backend/tests/integration/test_phone_widget_database.py backend/tests/integration/test_verified_phone_migration.py -q -p no:cacheprovider
if($LASTEXITCODE -ne 0){throw 'Database regressions failed.'}
npm run e2e
npx playwright show-report

# Database-independent UI audit; two known failures currently remain:
npm test
npm run build
npx playwright test --config playwright.public.config.ts
npx playwright show-report playwright-public-report
```

`npm run e2e` intentionally resets only the guarded local test database. Never run it in staging/AWS mode or with a production URL. Windows selector-loop and Alembic percent-escaping changes remain preserved. Passing this local harness verifies simulated storage/scanning/delivery boundaries only; real S3/GuardDuty/MSG91 need separately authorized verification.
