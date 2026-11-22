# Sign-in investigation and focused completion plan — 15 October 2026

## Verdict

Production sign-in is **BROKEN** for the reported request. Follow-up owner-supplied
metadata confirms the production schema is at `20260909_18` and users.auth_version
is missing, although the deployed baseline User query requires it. This is a
confirmed schema incompatibility sufficient to break the login lookup. The exact
original SQLSTATE was not provided. The misleading classification is fixed locally;
this is NOT a production sign-in repair or public-launch readiness claim.

Existing working-tree changes are preserved. No commit, push, deployment, production
migration, live login attempt, provider call or production data mutation was made.

### Follow-up: confirmed schema incompatibility

The owner's metadata output includes the existing users/user_roles/refresh_sessions
columns but no users.auth_version; Alembic reports `20260909_18`. Migration
`20261013_20` adds auth_version as a non-null integer with server default0;
`20261008_19` is its required predecessor and creates Terms acceptance records.
Thus the minimum existing migration-chain repair for this missing column is
18→19→20. Do not hand-add the column or stamp Alembic past unapplied migrations.

The inspected origin/main migration chain ends at22. Full baseline alignment also
requires21 (vehicle document table) and22 (phone ownership normalization/index and
constraint change). Migration22 locks users and modifies phone metadata; it can
refuse conflicting/invalid verified claims and needs impact review. It is not
necessary merely to add the missing login column.

Before ANY separately authorized production migration: confirm the SQL Editor and
API point to the same Neon project/branch/database, establish a verified restore
point/backup, test the bounded chain on isolated PostgreSQL, and review the exact
migration source. Current local head24 includes the provider re-verification policy
in23; do NOT run unbounded `upgrade head` from this dirty release candidate.
The existing GitHub production workflow runs `upgrade head` without a target input;
on inspected main that means22, NOT a bounded20 repair. No workflow was dispatched.

Next owner action is now restore-point/target confirmation, not another login
attempt. The SQL instructions below are retained as the historical investigation
step; the owner has completed them. Live login remains unverified until repair and
one controlled test. No additional application-code fix is needed to invent a
missing-column fallback; retain server-side session-version enforcement.

## Evidence and cause boundary

- The production homepage serves `/assets/index-840-LHTR.js`, which embeds
  `https://trucksetu-api-nine.vercel.app/api/v1`. It is not targeting a local API.
- Owner-supplied existing production Runtime Log: POST `/api/v1/auth/login`,
  `ProgrammingError`, Vercel displayed time `Oct 15, 13:44:08.090` (timezone not
  supplied), platform request ID `j24z8-1792052047829-8ca9f0ff9cc2`, deployment
  `dpl_CD4ndWxcQ27UARx23bSJvDbXXDDc`, branch main, Python3.12, bom1.
  The platform ID is not necessarily the application's X-Request-ID.
- Read-only checks at approximately **08:29:03–04 UTC**: `/health/ready` HTTP200,
  database/Redis available; `/version` HTTP200, build `ca`; `/openapi.json` HTTP200,
  legacy login present, cookie-session login absent. Readiness application request
  ID: `860430f5-b329-4ab8-a983-2924cb35161b`.
- Readiness executes a connectivity check, not a full schema or login transaction.
  These results do not contradict a login query failing with ProgrammingError.
- Confirmed code defect: the DBAPIError handler returned HTTP503/temporary outage
  for every database exception, including ProgrammingError. API detail is displayed
  by the existing frontend error parser. This explains the misleading UI message.
- Unconfirmed candidates: missing auth column/table, SQL/prepared-statement error,
  or other database programming defect. No SQLSTATE/diagnostic object name is in
  the supplied log. Do NOT assume a password problem, pool outage, specific missing
  migration, or that migrations23/24 will repair this login.
- Baseline origin/main models already require users.auth_version and the other
  identity/session columns. New cookie/shared acceptance work is uncommitted and
  unpushed; the deployed schema lacks cookie endpoints. `/version=ca` does not
  identify a valid deployed commit. The Vercel deployment source SHA was not
  accessible here; ccd594d remains the previously confirmed baseline, not a new
  independently verified production SHA.

SQLAlchemy2.0 [DBAPI error documentation](https://docs.sqlalchemy.org/en/20/errors.html)
distinguishes programming/schema errors from operational connection failures.

## Local changes and verification

- `backend/app/main.py`: ProgrammingError/nonavailability DBAPI failures now return
  controlled500; OperationalError, invalidated connections and pool timeout return
  controlled503. IntegrityError remains409. No login retry or permission relaxation.
- Logs contain exception class, validated five-character SQLSTATE (otherwise
  `unknown`), application request ID, method and route template. No raw exception,
  SQL, parameters, connection URL or identity values. Responses include a support
  request ID but no SQLSTATE/schema/internal details.
- `backend/tests/test_signin_error_mapping.py`: real FastAPI login/password/session
  code with isolated database and external-rate-limit fixtures. Tests success with
  API-returned provider role, wrong password401, programming500, operational503,
  integrity409, pool timeout503, invalid SQLSTATE and sensitive-value exclusion.
- RED: **4 failed/3 passed**, exposing false503, absent diagnostics and uncontrolled
  pool timeout. GREEN: focused auth/session group **34 passed**.
- Fresh complete nonintegration backend command: **331 passed**, two existing
  dependency deprecations (AnyIO portal alias/Alembic path_separator). Ruff passed;
  domain mypy passed. Frontend `npm test`: **46 passed**. `npm run build`: passed.
- Initial sandboxed pytest stalled and was terminated; the same test ran outside
  that restriction and produced the RED/GREEN evidence above.
- **BLOCKED:** real PostgreSQL auth/transaction/session tests: E2E_DATABASE_URL is
  absent in this process. No normal DATABASE_URL fallback, connection or reset.
- No fresh browser E2E or real AWS/SMS/email/payment verification in this task.
  Previous 37 synthetic browser passes and three simulated-scan KYC journeys are
  historical, not proof of the current deployed website or this exact working tree.

## Feature status

Status refers to the complete journey, not simply a route, page or unit test.

| Feature | Local status | Production status | Evidence | Remaining issue | Next fix | Owner | Acceptance check |
|---|---|---|---|---|---|---|---|
| Registration/sign-in | IMPLEMENTED BUT UNVERIFIED end-to-end | BROKEN sign-in; registration unverified | Fresh fixture login200/bad-password401; production ProgrammingError | Exact database query cause missing | Read-only schema/SQLSTATE correlation; repair proven defect only | Me supplies metadata; Codex diagnoses/fixes | Isolated DB success/bad password/unavailable; authorized deployed test account login |
| Persistent sessions/logout | IMPLEMENTED BUT UNVERIFIED | PARTIAL; new cookie routes absent | Fresh client/auth regressions; real DB cases authored | Persistence/revocation/browser-cookie deployment gates | Execute DB rotation/logout races and reopen/expiry journeys; release compatible pair | Codex + me for local DB/release | Reopen restores correct role; expiry/revoke/logout deny; CSRF rejected; account separation |
| Email verification/recovery | IMPLEMENTED BUT UNVERIFIED | IMPLEMENTED BUT UNVERIFIED | Existing adapter/UI and rejection-counter regressions | Actual SMTP acceptance/delivery and complete recovery not verified | Isolated recovery journey then authorized mailbox test | Codex + me for SMTP | Resend throttled; one-time expiry; password reset revokes sessions; no enumeration |
| Phone verification/trip OTP | IMPLEMENTED BUT UNVERIFIED | IMPLEMENTED BUT UNVERIFIED | Widget/backend validation and fake delivery boundaries exist | Real MSG91 widget/template acceptance/delivery unverified | Run approved test numbers only after provider configuration review | Codex + me for MSG91 | Server verifies token ownership; OTP not exposed; attempts/expiry enforced; acceptance not called delivery |
| Provider KYC/vehicle documents | IMPLEMENTED BUT UNVERIFIED with simulated scans | BLOCKED clean-scan journey | Historical fake KYC/review journeys; owner reports local S3 probe9 checks | No production scanner; version/eligibility rollout and real DB gates | Keep fail-closed; choose/configure real scanner; execute current version/assignment tests | Codex + me for scanner/rollout | Exact version clean plus all required unexpired documents manually accepted; private cross-provider denial |
| Requirements/quotes/customer acceptance | IMPLEMENTED BUT UNVERIFIED | IMPLEMENTED BUT UNVERIFIED; shared acceptance absent | Existing UI/API/snapshots; local regression evidence | No current real multi-role DB journey | Exercise revision/ownership/final amount acceptance | Codex; me supplies test DB | Accepted current provider quote creates exactly one unpaid booking with immutable breakdown |
| Full-vehicle booking/driver assignment | IMPLEMENTED BUT UNVERIFIED | IMPLEMENTED BUT UNVERIFIED | Existing backend authorization/eligibility tests | Current persisted customer/provider/driver journey unrun | Run allocations/assignment and driver-only access checks | Codex + me for DB | Correct eligible driver/vehicle only; strangers denied; no over-allocation |
| Shared publish/reserve/book/cancel/expire | IMPLEMENTED BUT UNVERIFIED | PARTIAL; new acceptance route not deployed | Local quote/hold/acceptance UI and locking code; nine DB scenarios authored | Real concurrency/release/expiry tests blocked; compatible rollout missing | Run migrations23/24 and DB scenarios locally, then complete controlled release | Codex + me for DB/release | No oversell; duplicates idempotent; current accepted quote snapshot; capacity released once |
| Pickup/delivery completion | IMPLEMENTED BUT UNVERIFIED | IMPLEMENTED BUT UNVERIFIED | Trip-state/OTP boundaries implemented | Multi-role persisted lifecycle and real delivery unverified | Run driver/customer lifecycle with fake delivery then approved sandbox | Codex + me for delivery | Assigned driver only; independent expiring limited OTPs; legal transitions, final completion |
| Payments/refunds/invoices | IMPLEMENTED BUT UNVERIFIED | IMPLEMENTED BUT UNVERIFIED | Captured webhook/idempotency/snapshot tests; printable invoice implementation | PostgreSQL financial snapshots and Razorpay sandbox reconciliation unverified | Run stored-value tests then approved payment/refund reconciliation | Codex + me for sandbox/legal | Amount/currency/signature correct; no duplicate funds; refunds recorded; original snapshots unchanged |
| Essential admin operations | PARTIAL | IMPLEMENTED BUT UNVERIFIED | Lists, KYC/vehicle review, refund/reactivation controls implemented | Full operator journeys and broader configuration scope unresolved | Verify minimum multi-role operations; resolve broader scope separately | Codex + me for scope | Server permissions/audits; queue/reasons/actions usable on mobile; no private-data leakage |

## Ordered completion work

1. **P0 — production sign-in:** obtain schema-only evidence below (or underlying
   SQLSTATE plus diagnostic table/column from an existing error); compare against
   the actual deployment source. Repair only the confirmed mismatch/query defect.
   No speculative production migrations. Retest locally, then request separate
   authorization for a reviewed release and one deployed test-account verification.
2. **P0 — unblock isolated verification:** configure restricted local transivox_e2e
   credentials privately and launch the agent from the same configured PowerShell,
   or run tests there. Use [exact setup/run commands](2026-10-15-release-candidate-verification.md).
   Execute migrations23/24, session/capacity races, KYC versioning and stored financial
   snapshots. Missing configuration is blocked, never passed.
3. **P1 — complete multi-role booking/trip and required shared-capacity journeys:**
   provider publication/quotation, customer explicit acceptance, assignment,
   cancellation/expiry and pickup/delivery. Shared capacity is NOT deferred.
4. **P1 — real private-file gate:** configure a supported scanner before real KYC
   registration/review approval can work. Preserve NO_THREATS_FOUND enforcement.
   Review migration23 impact: previously verified providers need resubmission;
   existing bookings/trips are preserved, new operations become gated. Audit
   production counts/impact before any separately authorized migration.
5. **P1 — external verification:** owner configures MSG91, SMTP and Razorpay sandbox;
   Codex verifies acceptance/delivery distinctions and payment/refund reconciliation
   only after authorization. IAM read permission is not application authorization.
6. **P1 — compatible release:** after DB gates, review/commit candidate under separate
   authorization; backup/impact review; migrate missing approved revisions once;
   compatible API then frontend from the same candidate. Verify SHA, routes, domain
   cookies, mobile roles and real integrations. No release action authorized here.
7. **P1 launch gates:** operational alerts, isolated backup restoration, independent
   security review and qualified policy/privacy/tax review. Google sign-in,
   phone-only sign-in, recurring requirements and broader admin configuration remain
   unresolved scope, not silently approved deferrals.

## Single next owner action: read-only auth schema check

Open the **Neon SQL Editor on the exact project/branch/database configured in the
production API**, not a similarly named test database. Run this read-only block.
It returns schema metadata and migration revision only; no user/session rows,
passwords, hashes, tokens or document records. Share only its result tables/error
class/SQLSTATE, never the connection URL or credentials. I have NOT executed this
against production.

```sql
BEGIN READ ONLY;
SET LOCAL statement_timeout = '5s';
SELECT table_schema, table_name, column_name
FROM information_schema.columns
WHERE table_schema = 'public'
  AND table_name IN ('users', 'user_roles', 'refresh_sessions')
ORDER BY table_name, ordinal_position;
SELECT version_num FROM public.alembic_version;
ROLLBACK;
```

If a query errors, issue `ROLLBACK;` before leaving the SQL Editor. If metadata
matches, the next necessary evidence is the underlying SQLSTATE/diagnostic object
from existing database error logs; matching metadata does not exclude query or
prepared-statement errors. Do not re-run login to generate an error.

## Safe local rerun (no database required)

From the repository root in PowerShell:

```powershell
$env:PYTHONPATH='backend'
& .\.venv\Scripts\python.exe -m pytest backend/tests/test_signin_error_mapping.py -q -p no:cacheprovider
& .\.venv\Scripts\python.exe -m pytest backend/tests --ignore=backend/tests/integration -q -p no:cacheprovider
& .\.venv\Scripts\python.exe -m ruff check backend/app backend/tests backend/migrations
& .\.venv\Scripts\python.exe -m mypy backend/app/domain.py
npm test
npm run build
```
