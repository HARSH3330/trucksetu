# Database/login readiness follow-up — 15 October 2026

Scope: database binding, bounded repair review, retained recovery and isolated
candidate checks. No production/recovery writes, branch reset/creation, migration
execution, deployment, push, SMS, payments or AWS operations in this follow-up.
Existing working-tree changes are preserved. The owner's latest message ends at
"Determine whether the recovery point is sufficiently current and"; no missing
authority is inferred.

## Checklist and fresh evidence

- [x] API alias still resolves to READY production deployment
  `dpl_CD4ndWxcQ27UARx23bSJvDbXXDDc`, source
  `ccd594df8a78f56041876c058b522e0624db4fb6`.
- [ ] Actual runtime DATABASE_URL binding conclusively established. Existing
  sensitive-variable metadata is insufficient. Runtime log search for the known
  endpoint over 1d returned HTTP400: Hobby does not retain that time range. A
  corrected 30m query supplied no hostname/database evidence. Source readiness
  executes SELECT1 only; it cannot identify a branch/database. No secret readback
  or Preview write test was attempted.
- [x] Explicit Neon project/branch/compute mappings rechecked before schema reads:

| Target | Branch | Compute | Database | Revision |
|---|---|---|---|---|
| production | br-polished-surf-axulzu38 | ep-fragrant-surf-axkjz078 | neondb | 20260909_18 |
| retained recovery | br-morning-base-ax0dr2z2 | ep-purple-pond-ax3menwy | neondb | 20260909_18 |
| rehearsal | br-weathered-hill-axdizmg3 | ep-dry-frog-ax9mkld2 | neondb | 20261014_22 |

Production lacks users.auth_version, terms_acceptances and vehicle_documents;
users_mobile_key is present. Pinned deployed User model selects auth_version.
This establishes schema incompatibility on the intended Neon production target,
not independent proof of the API's actual saved connection string.

## Bounded migrations: exact code and impact

Pinned checkout .tmp/production-schema-ccd594d is clean at the exact deployed SHA.
Current candidate's migration19–22 files and migration environment have no diff
from that SHA. Candidate HEAD d5f4306 and uncommitted session/shared-acceptance work
must not replace this bounded repair source. Candidate head24 is NOT the repair
target.

| Revision | Upgrade behavior | Lock/compatibility considerations |
|---|---|---|
| 19 | Creates Terms acceptance table and unique user/version index | New table; FK references users and takes referenced-table locks. No existing acceptance evidence is fabricated. |
| 20 | Adds non-null users.auth_version with constant default0 | ALTER TABLE requires a strong table lock; PostgreSQL constant-default optimization does not remove locking. No passwords/sessions are deleted. |
| 21 | Creates private vehicle-document table, FKs and index | References users/carrier_vehicles; does not approve documents or backfill existing vehicles. New VersionId column is mandatory for new vehicle documents. |
| 22 | Locks users; refuses invalid/conflicting verified phones; replaces global mobile uniqueness with verified-only uniqueness; canonicalizes valid numbers | Explicit ACCESS EXCLUSIVE users lock blocks reads/writes while held. UPDATE rewrites qualifying user rows. Index/check creation scans data. Expected production normalization affects one row; no phone value was returned. |

All four upgrades use Alembic's PostgreSQL transactional DDL path. A failure in
this single bounded transaction must roll back; do not use autocommit, stamp,
upgrade head, manual replacement DDL or automatic retries. Earlier table/FK locks
remain relevant until commit. Configure finite lock/statement timeouts on the
DIRECT connection, not the pooled runtime URL.

Migration22 downgrade is not a general recovery strategy: later unverified
duplicate phone claims can prevent restoring global uniqueness. Never delete
claims or choose a verified winner to force either direction.

## Prior rehearsal applicability, freshly checked

The integration-blockers handoff records the original 18→22 execution: actual
repository Alembic offline SQL applied in one MCP transaction; server duration
0.101510s, round trip6.110s. Those timings are HISTORICAL, not fresh production
lock measurements or an online psycopg/CLI test.

Fresh offline regeneration from the clean pinned checkout matches the retained
2026-10-15-migration-18-to-22.generated.sql after line-end trailing-whitespace
normalization. Initial byte comparison failed only for trailing spaces emitted
in CREATE TABLE lines; no statement/content mismatch was found. Pinned pip check
also passes.

Fresh independent rehearsal postconditions: revision22; auth_version non-null,
default0, no nonzero versions; Terms and vehicle-document tables empty; legacy
phone unique constraint absent; canonical-phone CHECK and verified-only partial
unique index present. Migration23 KYC VersionId column remains absent.

Rehearsal is already22. It was not reset, downgraded, stamped, or migrated again.
A fresh 18→22 execution would require an explicitly approved fresh branch or
reviewed reset; none was inferred. The existing execution artifact plus matching
source/postconditions supports the earlier rehearsal, not a new execution claim.

## Recovery/read-only preservation checks

Recovery parent is production; copy point 2026-10-15T08:51:56Z, LSN0/2A6AB30.
Rehearsal parent is production; copy point17:14:23Z, LSN0/2AB7FA8. Endpoints differ.
No expiry is reported; protected=false. Project history window is21600s (6h),
not a promise that any historical timestamp remains restorable indefinitely.

Fresh aggregates match across all three databases: users4, roles4, sessions12
(8 revoked), audit1, providers/bookings/allocations/trips/vehicles0. Latest user,
login and session creation timestamps also match. Invalid verified-phone claims0;
conflicting canonical verified groups0. No personal values or row contents were
returned. Historical evidence additionally records unchanged counts for47 old
tables; that full count sweep was not repeated here.

Counts/timestamps cannot detect all in-place password/profile/permission changes.
Therefore recovery is readable and retained, but its freshness is NOT certified.
Keep it unchanged. Before production execution, obtain approval for a fresh
pre-execution recovery point/new branch and validate it; do not overwrite this
copy. This is not an independently verified historical restore.

## Fresh isolated checks

- Pinned dependency check: PASS.
- Bounded offline regeneration/artifact semantic comparison: PASS.
- test_phase20_migrations.py: 3 passed, one Alembic configuration warning.
- test_signin_error_mapping.py + test_cookie_sessions.py: 24 passed, one existing
  Starlette/AnyIO deprecation warning. These use fake database/auth fixtures;
  successful login, wrong-password401, database503/schema500 mapping, cookie/CSRF
  boundaries are not real PostgreSQL or browser persistence verification.
- test_shared_acceptance.py, test_shared_quote_contract.py,
  test_shared_quote_revision.py, test_settlement_snapshots.py: 19 passed. These
  simulate persistence boundaries; they do not prove database races/transactions.
- Initial TestClient runs stalled before application execution in Windows event
  loop socket-pair creation inside the sandbox. Stopped those owned sessions;
  the same focused tests passed outside that sandbox restriction. No application
  bypass, timeout increase or authentication weakening was introduced.
- E2E_DATABASE_URL absent: real PostgreSQL session/shared/financial/migration23/24
  tests and local Playwright database journeys BLOCKED, not passed. No fallback
  to application DATABASE_URL or Neon. E2E_REAL_AWS=false for local checks.

## Concrete production plan — not execution approval

1. Owner privately confirms the API Production DATABASE_URL's original saved
   source targets ep-fragrant-surf-axkjz078[-pooler].c-4.us-east-2.aws.neon.tech,
   path /neondb. Check effective environment override too. Report only MATCH or
   MISMATCH, never the URL/password. If the saved Secret cannot be viewed and its
   source is unavailable, binding remains blocked pending a separately approved
   sanitized runtime diagnostic; do not rotate/redeploy just to infer it.
2. Approve and verify a fresh recovery point, retain the existing copy, designate
   one operator and a low-traffic lock window. Recheck revision18/phone preflight.
3. After separate production execution approval, use the clean pinned Python and
   DIRECT target via masked process environment; finite lock_timeout5s and
   statement_timeout60s, sanitized errors. From the pinned backend run:
   `python -m alembic -c alembic.ini current`, then
   `python -m alembic -c alembic.ini upgrade 20261014_22`, then `current`.
   Stop on any failure; do not run from candidate head24 or use upgrade head.
4. Verify schema/postconditions and aggregate preservation, then readiness and
   one controlled website login, API role, restoration and logout. No real login
   attempt or production repair occurred during this follow-up.
5. If transaction fails, verify rollback/revision before any retry. If recovery
   after commit is needed, stop writes; separately approve a NEW recovery-derived
   branch/cutover and reconcile post-copy writes. Do not blindly downgrade or
   repoint the API at the retained recovery copy.

For isolated test setup and launching a process with E2E_DATABASE_URL, reuse
2026-10-15-release-candidate-verification.md. Set variables in the same PowerShell
session that launches Codex or runs tests; a separate terminal cannot inject them
into an already-running desktop process. Do not use Preview as a substitute.
