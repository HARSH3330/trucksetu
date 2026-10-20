# Integration blockers — bounded execution handoff, 15 October 2026

## Execution ledger / authority

Plan: owner's three-phase database/login → MSG91 → deployed KYC instructions.
Preserve dirty release candidate; no commits/push/deploy. One migration operator.
Rehearsal22 is authorized ONLY after endpoint/branch verification. Production22
requires a new, explicit execution approval after successful rehearsal.
Recovery copy must remain unchanged. Never run upgrade head or migrations23/24.

- Phase1: authenticated Neon mappings and bounded rehearsal22 verified (see update
  below). Production execution remains unapproved and was NOT performed.
- Phase2 code inspection and fake-boundary checks: complete; real SMS NOT executed.
- Phase3 source inspection/test preparation: complete; deployed upload NOT executed.
- Ruling: retain existing pinned checkout and masked checker; do not invent Neon
  branch IDs, fetch secret connection strings into chat, or bypass MCP authentication.
- No application defect newly reproduced in this continuation; no speculative code
  changes. Existing local changes, including KYC immutable-version fix, preserved.

## Authenticated rehearsal update — 15 October, 22:48 IST

### Subsequent authenticated Vercel inspection

Vercel connection now works. Read-only team/project/deployment lookups verified
API project trucksetu-api (`prj_gXnKmzBiPf8TpQ5MJmZLQPg04diF`), team
harsh3330s-projects (`team_iu09mmhsbf90RQTBtkgvOHlX`). Alias
trucksetu-api-nine.vercel.app resolves to production deployment
`dpl_CD4ndWxcQ27UARx23bSJvDbXXDDc`, READY, main source SHA
`ccd594df8a78f56041876c058b522e0624db4fb6`. Pinned source compatibility is now
freshly confirmed independently of the broken /version build label.

Only environment metadata was requested (`decrypt=false`); no secret-value
retrieval. DATABASE_URL and MIGRATION_DATABASE_URL are present as sensitive values,
each scoped to BOTH production and preview. DATABASE_URL metadata last updated
2026-08-23T17:33:32.312Z. Sensitive values cannot be read back, so the actual
hostname/database in the saved secret remain unverified through this connection.
Do not infer the value from its name, presence, old logs or readiness. No further
plugin installation fixes this read-back restriction. Owner source confirmation
or a separately approved private diagnostic/configuration action is still needed.

Preview isolation concern: the same DATABASE_URL entry is assigned to Production
and Preview. Do not use Preview for write/E2E verification until separately
configured for an isolated staging database under explicit change authorization.
No environment value/scope, deployment or database was changed during inspection.

This supersedes the earlier Auth-required blocker below. MCP project lookup and
explicit branch/database queries now succeed. Project **Trucksetu**:
`morning-forest-29164100`, aws-us-east-2; database **neondb** on every checked branch.

| Purpose | Branch ID | Endpoint ID / direct hostname | Actual revision |
|---|---|---|---|
| Production | br-polished-surf-axulzu38 | ep-fragrant-surf-axkjz078 / ep-fragrant-surf-axkjz078.c-4.us-east-2.aws.neon.tech | 20260909_18, unchanged |
| Retained recovery pre-migration-20261015 | br-morning-base-ax0dr2z2 | ep-purple-pond-ax3menwy / ep-purple-pond-ax3menwy.c-4.us-east-2.aws.neon.tech | 20260909_18, unchanged |
| Approved rehearsal migration-rehearsal-20261015 | br-weathered-hill-axdizmg3 | ep-dry-frog-ax9mkld2 / ep-dry-frog-ax9mkld2.c-4.us-east-2.aws.neon.tech | 18 before; 20261014_22 after |

The production pooled hostname is the same endpoint with `-pooler` before the first
dot. It matches the previously reported runtime hostname, but current Vercel
DATABASE_URL was NOT accessible for a fresh private comparison. Confirm its host
and neondb before production execution; no secret values are needed in chat.

### Branch identity, retention and creation

- Initial complete branch listing had only production and recovery: the intended
  rehearsal did not exist. Owner explicitly approved creating the isolated normal
  branch, including possible branch/compute cost.
- Recovery parent is production, copy LSN `0/2A6AB30`, copy timestamp
  **2026-10-15T08:51:56Z** (14:21:56 IST). Rechecked accessible and still revision18.
  It was not reset, renamed, migrated or deleted. SELECTs can wake compute/update
  platform last-access metadata; no application schema/rows were written.
- Rehearsal parent is production, copy LSN `0/2AB7FA8`, copy timestamp
  **2026-10-15T17:14:23Z**, created17:15:05Z. Parent-data normal copy, distinct host.
- First creation attempt explicitly setting suspend_timeout_seconds=300 failed412:
  account plan forbids changing that interval. Verified no partial branch existed;
  retry with only min/max0.25CU succeeded. Actual min/max0.25; suspend_timeout_seconds
  reports0 (account/platform default); actual idle auto-suspend interval is NOT
  verified. No account upgrade/security change was performed.
- Detailed get_branch records returned no expires_at value for these branches.
  No expiration was set or changed. All three report protected=false. This is not
  a retention/protection guarantee. Project history window reports21600s (6h),
  separate from retained branch lifetime; do not confuse the two. Recovery remains
  a current-state copy, NOT independently tested historical restoration.

### Rehearsal execution and timing

- Clean pinned source rechecked at ccd594df8a78f56041876c058b522e0624db4fb6.
  Existing dependency/offline test passes were reused, not another broad test run.
- With no locally prompted credentials, generated the executable SQL from the
  pinned repository's actual Alembic `command.upgrade(...,
  '20260909_18:20261014_22', sql=True)` and applied its15 emitted statements through
  authenticated Neon MCP in ONE transaction. No handwritten replacement schema,
  direct manual version stamp or get-connection-string call. The version-table
  updates were emitted by Alembic alongside their actual DDL/data migrations.
- This is an **executed Alembic offline-script rehearsal over MCP**, not an online
  psycopg/Alembic-CLI connection test. Migration wrapper BEGIN/COMMIT was supplied by
  MCP's transaction; emitted DDL/data statements were unchanged. The extra wrapper
  only enforced database/revision preconditions, advisory ownership and timeouts.
- Explicit project, branch AND endpoint IDs used; guarded starting revision18 and
  current_database=neondb; advisory transaction migration lock; lock_timeout5s and
  statement_timeout60s. Production/recovery never received the mutation payload.
- Server migration start **17:18:49.266382Z**, finish **17:18:49.367Z**;
  measured duration **0.101510 seconds**, whole MCP round trip **6.110 seconds**.
  No lock timeout or migration error. This does NOT predict production lock timing
  under contention.22's ACCESS EXCLUSIVE users lock remains a release impact.
- Retained review artifact: `2026-10-15-migration-18-to-22.generated.sql` in this
  directory. It is generated migration output, NOT instructions to run SQL manually.

### Post-commit verification (independent read-only requests)

- Rehearsal revision exactly22, database neondb. All13 expected User/login columns
  present. auth_version nullable=NO, default0, all4 users retain version0.
- terms_acceptances and vehicle_documents exist, both empty as expected.
- Legacy users_mobile_key removed; ck_users_verified_mobile_canonical present;
  uq_users_verified_mobile partial unique index includes WHERE mobile_verified.
- Production and recovery phone preflight: invalid verified claims0, canonical
  verified conflicts0, legacy unique constraint present before upgrade. Migration22
  also ran its own transactional conflict guards successfully on rehearsal.
- KYC storage_version_id from migration23 is absent;23/24 were not applied.
- Row counts for **all47 pre-existing non-Alembic public tables** unchanged on
  rehearsal; also rechecked unchanged on production and recovery. Nonempty tables:
  users4, user_roles4, refresh_sessions12, account_verifications3, audit_logs1,
  application_settings1, trip_price_estimates3. Bookings/trips/providers/vehicles
  and other checked tables have0 rows. New tables empty. No deleted records shown.
- Limitation: full-row preservation fingerprinting was rejected by the safety
  reviewer because it scans sensitive auth/KYC/message/financial contents. After
  the explicit rejection, used only the approved counts/schema alternative; no
  bypass. **Counts and reviewed SQL are not row-for-row content preservation
  proof.** A deeper comparison needs a narrowly scoped privacy-reviewed method
  and approval before attempting it. No personal fields or auth hashes printed.
- Real website login NOT attempted; production still lacks auth_version and no
  production migration approval has been given. No SMS, AWS objects, KYC scan
  override, push, deployment or production/reset operation occurred.

### Exact production proposal — NOT EXECUTED

Target: project morning-forest-29164100; production branch
br-polished-surf-axulzu38; direct endpoint ep-fragrant-surf-axkjz078; neondb;
source **ccd594df8a78f56041876c058b522e0624db4fb6**;
bounded target20261014_22, starting18.

For owner-operated online Alembic, privately supply/validate the direct production
MIGRATION_DATABASE_URL using masked local input, verify that exact host/database,
and set APP_ENV=development/DEBUG=false for this isolated migration process (NOT
the deployed API). Then, from the repository root:

```powershell
$taskPinnedPython=(Resolve-Path '.tmp/production-schema-ccd594d/.venv/Scripts/python.exe').Path
Push-Location '.tmp/production-schema-ccd594d/backend'
try {
  & $taskPinnedPython -m alembic -c alembic.ini current
  if($LASTEXITCODE -ne 0){throw 'Stop: cannot confirm starting revision'}
  # Execute ONLY after target/recovery checks and explicit production approval.
  & $taskPinnedPython -m alembic -c alembic.ini upgrade 20261014_22
  if($LASTEXITCODE -ne 0){throw 'Stop: migration failed; no automatic retry'}
  & $taskPinnedPython -m alembic -c alembic.ini current
} finally { Pop-Location }
```

Alternatively use the same reviewed generated payload via MCP with explicitly
pinned production branch/endpoint and the same transaction guards, after approval.
No need to expose/fetch database passwords for that method. Do not use upgrade head.

Before execution: (1) confirm CURRENT Vercel production hostname/database,
(2) recheck production revision18, phone conflicts and no competing migrator,
(3) verify recovery freshness. Recovery's copy is over8h old at rehearsal; matching
row counts alone cannot prove no intervening updates. Preserve it unchanged. A
fresh separately approved recovery copy/restore point is preferable; do not create
or reset one without permission, and do not rely solely on the6h history window.
(4) Explicitly approve target22 and lock impact; schedule a short controlled window.

Recovery: transaction failure must roll back and be inspected before retry; after
commit, an approved rollback/cutover must use a NEW branch derived from retained
recovery and reconcile writes since its copy point. Never reset production, stamp
revision, blindly downgrade22, or repoint the API without separate authorization.

After approved production execution: independently verify revision/schema/indexes,
counts, readiness, then one designated website login/role/refresh/logout journey.
Rehearsal schema success and readiness200 are NOT production login verification.

## Fresh evidence (not historical test results)

1. `.tmp/production-schema-ccd594d` is clean and its HEAD is
   `ccd594df8a78f56041876c058b522e0624db4fb6`. Existing .venv is Python3.12.14.
2. The .venv initially had psycopg but lacked Alembic/SQLAlchemy/FastAPI/settings.
   Installed that checkout's requirements into ONLY that .venv, constrained
   SQLAlchemy<2.1 consistently with project metadata. `pip check` passed. Pip warned
   that psycopg does not provide the legacy `asyncio` extra; binary driver installed.
3. Pinned offline command `alembic upgrade 20260909_18:20261014_22 --sql` passed;
   exactly19,20,21,22 compiled. Pinned head is22. No database connection or writes.
4. Production API read-only GET checks at 17:04:08–10 UTC (22:34 IST): readiness200,
   PostgreSQL/Redis available; version200/build `ca`; OpenAPI200 with phone widget
   verification and KYC upload routes, no cookie-session login route.
   Readiness X-Request-ID `a3c77362-2f23-470a-9be1-2e0ff8623bf5`.
   This is NOT fresh authentication/schema/S3 proof. Exact deployed source SHA
   remains unverified; ccd594d is the last verified production baseline.
5. Focused local tests: **25 passed**, existing AnyIO deprecation warning:
   test_msg91_widget.py, test_trip_otp_delivery.py, test_kyc_versions.py,
   test_storage_configuration.py. These use fake external services, NOT Neon/AWS/SMS.
6. Neon plugin is installed and enabled (confirmed via plugin metadata), but its
   MCP runtime initialization fails with **Auth required**. No project list,
   branch metadata or SQL access succeeded. No authenticated browser tab exists.
   No database/Neon credentials are present in this process. Owner's ChatGPT-side
   connection does not establish a usable authenticated MCP session here.

## Phase1: exact remaining verification and approval gate

Known only from owner/historical evidence: runtime DATABASE_URL database neondb,
revision18, missing users.auth_version; recovery pre-migration-20261015;
intended rehearsal migration-rehearsal-20261015. These names are NOT verified IDs.

After MCP authentication succeeds, read project/branch/endpoint metadata and record:

| Target | Required evidence before any migration |
|---|---|
| Production | Neon project ID, branch ID/name, endpoint ID/host, neondb; privately compare actual Vercel DATABASE_URL host to endpoint; branch name alone is insufficient |
| Recovery | pre-migration-20261015 branch ID, parent ID/LSN/time, retained lifecycle/expiration, separate endpoint, neondb read-only connectivity/revision/schema |
| Rehearsal | migration-rehearsal-20261015 exists; expected parent ID and copy point; endpoint differs from production AND recovery; neondb read-only connectivity and current revision/schema |

Do not call get-connection-string tools that print credentials. If local direct
connections are needed, reuse `.tmp/verify-rehearsal-readonly.ps1` masked input.
That checker proves URL target separation and read-only DB access, NOT branch
parentage, recovery retention or Vercel environment mapping. Never substitute it
for Neon control-plane metadata. No branch reset/create/delete is needed by default.

On verified rehearsal, collect before/after counts for users, user_roles,
refresh_sessions, providers, bookings, allocations, trips, vehicles and audit history
using their actual schema names. Compare IDs/unchanged fields privately, emitting
only equality results; counts alone do not prove full data preservation. Exclude
the approved mobile normalization and new default auth_version from unchanged-field
comparisons. Do not print phones, email, hashes, tokens or row contents.

Read-only phone preflight (on the verified target; aggregate-only output):

```sql
BEGIN READ ONLY;
SET LOCAL statement_timeout = '5s';
WITH phones AS (
  SELECT mobile_verified,
         (mobile IS NULL OR mobile !~ '^\+?[1-9][0-9]{7,14}$') AS invalid,
         CASE WHEN mobile !~ '^\+' AND length(mobile)=10
              THEN '+91'||mobile ELSE '+'||ltrim(mobile,'+') END AS canonical
  FROM public.users
), conflicts AS (
  SELECT canonical FROM phones WHERE mobile_verified
  GROUP BY canonical HAVING count(*) > 1
)
SELECT (SELECT count(*) FROM phones WHERE mobile_verified AND invalid)
         AS invalid_verified_claims,
       (SELECT count(*) FROM conflicts) AS conflicting_verified_groups;
ROLLBACK;
```

Both must be zero; never select a winner, delete users or silently unverify them.
Confirm users_mobile_key exists before22, plus actual current revision and schema.
Record rehearsal start/end UTC, elapsed time, row counts and lock wait/result.

Prepared command, **NOT executed and NOT production approval**:

```powershell
# Only after verified direct rehearsal target is supplied privately to
# MIGRATION_DATABASE_URL and APP_ENV/DEBUG are explicitly configured.
$taskPinnedPython=(Resolve-Path '.tmp/production-schema-ccd594d/.venv/Scripts/python.exe').Path
Push-Location '.tmp/production-schema-ccd594d/backend'
try {
  & $taskPinnedPython -m alembic -c alembic.ini current
  if($LASTEXITCODE -ne 0){throw 'Stop: current revision check failed'}
  & $taskPinnedPython -m alembic -c alembic.ini upgrade 20261014_22
  if($LASTEXITCODE -ne 0){throw 'Stop: bounded migration failed; inspect sanitized diagnostics'}
  & $taskPinnedPython -m alembic -c alembic.ini current
} finally { Pop-Location }
```

Preflight must require starting revision18 for this rehearsed path; do not run the
example with missing target configuration because application settings have a
development URL fallback. Operator must configure finite lock/statement limits,
verify target, and suppress raw credential-bearing exception output. This is a
reviewed command outline, not an unattended migration runner.

Lock impact:22 obtains ACCESS EXCLUSIVE on users and updates valid mobile values;
earlier ALTER TABLE can also hold locks until transaction commit. Reads/sign-in
can wait; actual duration is UNKNOWN until rehearsal. Never automatically retry a
failed production migration or extend timeouts without diagnosing lock contention.

After rehearsal passes, present exact production branch/endpoint/neondb, pinned
SHA/target22, elapsed/lock evidence, preflight and recovery freshness. Obtain owner
approval. Before execution recheck production schema/phone conflicts, recovery
retention/readability/copy-point freshness, and ensure no concurrent migration.

Recovery procedure: keep recovery unchanged; if migration transaction fails,
inspect rollback/revision and remain on the existing target until reviewed. If
recovery is required after commit, stop writes and plan a separately approved
restoration/cutover using a NEW branch derived from recovery, reconcile all writes
since its copy point, then update the API target only under explicit approval.
Do NOT blindly downgrade22 or point the API at the retained recovery branch.
Current-state branch accessibility is NOT a successful historical restore test.

Post-migration: verify22, users.auth_version default/non-null, Terms/vehicle tables,
phone constraint/index, unchanged business records; readiness; then ONE controlled
website login using masked credentials, API role/session restoration and logout.
No account retries or login claim based on readiness alone.

## Phase2: MSG91 preparation

Actual missing deployment variables are UNKNOWN: Vercel environment access absent.
Only these integration-specific inputs need presence/configuration confirmation:

| Flow | Frontend public | API-only | Additional prerequisite |
|---|---|---|---|
| Signed-in saved-phone verification | VITE_MSG91_WIDGET_ID, VITE_MSG91_WIDGET_TOKEN_AUTH | MSG91_WIDGET_ENABLED=true, MSG91_AUTH_KEY (secret) | Widget allowed origins include https://www.transivox.in and any deliberately supported apex; valid account mobile |
| Trip pickup/delivery OTP | none | MSG91_AUTH_KEY (secret), MSG91_TEMPLATE_ID, MSG91_OTP_VARIABLE (defaults OTP) | Approved Flow/DLT template and sender/entity setup; field name matches actual template, not mobiles |
| OTP-only login | none | none | NOT IMPLEMENTED; do not describe signed-in verification as phone-only login |

The API verifies widget proof at MSG91 before marking the matching saved mobile
verified. POST /api/v1/auth/mobile/verify-widget requires existing authentication.
Widget JavaScript success is not sufficient. Reused/mismatched proof must fail.

Trip issue: POST /api/v1/trips/{trip_id}/otp/{pickup|delivery}; verify:
POST /api/v1/trips/{trip_id}/otp/verify. Existing legal trip status and authorized
booking parties required. Endpoint sends to the booking customer's saved mobile;
use a designated fictional booking/test account with the approved test number,
never an existing customer's booking. Do not create production trip records yet.

Before sending: owner designates number privately, approves one send/flow and
possible charge, confirms template approval and environment. Test actual handset
receipt separately from provider acceptance. Confirm expiry, single use, attempts,
correct server validation and persisted verification/trip state. Never retain OTPs
or proof tokens in reports. Current code reports accepted + delivery unconfirmed;
there is NO inbound MSG91 delivery-report webhook. No SMS was sent.

## Phase3: KYC preparation and scanner decision

Important source gap: at pinned ccd594d provider KYC registration/review/download
calls storage without VersionId, although the adapter supports version reads.
Vehicle-document code DOES store/pass VersionId. Local provider-KYC candidate
pins versions and has fresh passing simulated regressions; it is not deployed.
An explicit reviewed compatible API/schema release is required before claiming
deployed immutable provider-KYC evidence. Actual deployment SHA needs confirmation.

Prepared designated scenario (NO writes executed): choose dedicated provider
account/owner application; generate a valid PDF with existing
e2e/fixtures/pdf.ts, visibly NOT A REAL IDENTITY DOCUMENT; request KYC upload URL,
PUT with Content-Type and x-amz-server-side-encryption:AES256, retain exact VersionId
privately; verify unsigned access denied and application registration409 while
scan absent. Capture only sanitized IDs/statuses, not signed URLs or credentials.
Expected write set after separate approval: designated test account if absent,
provider profile/application, one unique harmless S3 object under that provider's
kyc/ prefix. The actual website creates kyc/{provider_id}/{type}/ keys, not the
standalone-probe kyc/test/ prefix. Approve that exact test namespace first.
Blocked registration must create no KYCDocument row; full approval remains blocked.

Scanner contract: API AWS_S3_BUCKET=transivox-kyc-harsh3330,
AWS_REGION=ap-south-1; private/versioned/encrypted bucket; kyc/ objects.
It reads exact-version GuardDutyMalwareScanStatus and permits only
NO_THREATS_FOUND. Missing, failed, unsupported, access-denied or threats stay blocked.
There is NO scanner URL/key/toggle or inbound scan webhook in application code.

AWS setup if owner approves availability/cost: GuardDuty Malware Protection for S3
in ap-south-1 on that bucket, prefix kyc/, **Tag objects enabled**, service role
with required read/tag/EventBridge access and plan ACTIVE. Keep uploader/API identity
unable to forge clean-scan tags; retain version-specific read/tag permissions.
[AWS setup](https://docs.aws.amazon.com/guardduty/latest/ug/enable-malware-protection-s3-bucket.html).

AWS documents a monthly scan free allowance (1GB/1,000 requests), but S3 API/tagging
and EventBridge charges are excluded and excess scanning is billable. This does
NOT prove the owner's Free account plan can enable the service. Verify exact
console restriction before changing account plan or enabling any paid service.
[AWS pricing](https://docs.aws.amazon.com/guardduty/latest/ug/pricing-malware-protection-for-s3-guardduty.html).

If unavailable: (1) owner-approved account-plan upgrade + native GuardDuty is the
smallest contract change; (2) a separately designed private version-bound scanner
(e.g. managed scanner or isolated ClamAV worker) requires adapter/security/replay/
quarantine tests, operational monitoring and compute/licensing costs; not just
manually writing a GuardDuty clean tag; (3) leave KYC completion unavailable.
Do not adopt an alternative, send private identity files to a third party or
weaken scanning without explicit cost/privacy/security approval.
