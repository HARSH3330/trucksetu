# Bounded Production Database Repair and API Redeployment Plan

> **For agentic workers:** Execute with superpowers:executing-plans only after
> explicit owner approval of the external operations below. Use the primary
> agent; no delegation, commit or push is authorized. Steps are approval gates.

**Goal:** Repair the deployed revision22 API's database compatibility, reload
the owner-confirmed production connection setting, and verify one controlled
login without releasing the unfinished candidate.

**Architecture:** Fresh independent Neon recovery branch, then the exact
rehearsed Alembic-generated18→22 transaction on production, then a same-source
Vercel API redeployment using current Production settings. The frontend and
retained recovery/rehearsal branches remain unchanged.

**Tech stack:** Neon PostgreSQL, repository Alembic migrations, FastAPI, Vercel.

**Spec:** Owner's saved-configuration confirmation and approval-plan request;
docs/testing/2026-10-15-database-readiness-followup.md;
docs/testing/2026-10-15-integration-blockers.md.

## Global constraints

- PREPARED ONLY. Creating the recovery branch, production SQL writes and API
  redeployment are not yet approved or executed.
- SHA: ccd594df8a78f56041876c058b522e0624db4fb6, not local d5f4306/candidate head24.
- Migration source: clean .tmp/production-schema-ccd594d; target20261014_22.
- Never upgrade head, run23/24, stamp, downgrade, reset or delete records/branches.
- No Preview writes, frontend redeploy, SMS, payments, S3 upload or scan override.
- Credentials stay out of tool output, logs and command arguments.
- Shared capacity remains required; its candidate release is a separate gate.

## Current evidence and limitations

Owner confirms replacing the Production DATABASE_URL with the Neon production
endpoint/neondb string, with no subsequent deployment. Treat saved target as
OWNER-CONFIRMED, not independently read back or proven for the running release.

Fresh alias lookup still returns READY deployment
dpl_CD4ndWxcQ27UARx23bSJvDbXXDDc at the pinned SHA. Fresh decrypt=false metadata
lists DATABASE_URL AND MIGRATION_DATABASE_URL as sensitive entries scoped to
both production and preview. This differs from the owner's Production-only scope
description. Do not change scopes silently; keep Preview excluded. Secret values
were not fetched. Vercel's migration variable is not used to infer a SQL target.

Previous-session checks: intended production/recovery revision18, rehearsal22;
phone-conflict aggregates0; reviewed SQL identical after trailing-whitespace
normalization; 46 local fake-boundary/offline checks passed. Those are historical
for execution approval and must not be described as newly rerun checks here.
Real local PostgreSQL candidate tests remain blocked by absent E2E_DATABASE_URL.

## Exact targets

| Purpose | Target |
|---|---|
| Neon project | morning-forest-29164100 (Trucksetu) |
| Production branch | br-polished-surf-axulzu38 |
| Production compute | ep-fragrant-surf-axkjz078 |
| Direct host | ep-fragrant-surf-axkjz078.c-4.us-east-2.aws.neon.tech |
| Runtime pooled host | ep-fragrant-surf-axkjz078-pooler.c-4.us-east-2.aws.neon.tech |
| Database | neondb |
| Retain unchanged | pre-migration-20261015 / br-morning-base-ax0dr2z2 |
| Retain unchanged | migration-rehearsal-20261015 / br-weathered-hill-axdizmg3 |
| Proposed NEW recovery | pre-repair-22-20261015, parent production at current HEAD |
| Vercel team | team_iu09mmhsbf90RQTBtkgvOHlX |
| API project | trucksetu-api / prj_gXnKmzBiPf8TpQ5MJmZLQPg04diF |
| API production alias | trucksetu-api-nine.vercel.app |
| Website, unchanged | www.transivox.in / trucksetu-whri |

## Review focus

1. Stale database binding: new deployment must load CURRENT Production settings;
   readiness alone cannot prove the endpoint or successful authentication.
2. Stale recovery: capture immediately before mutation, record copy LSN/time and
   verify a separate endpoint; counts alone are not a full content/restore proof.
3. Lock contention: users ACCESS EXCLUSIVE can block sign-in; bounded timeouts,
   single operator, no blind retry or forced termination of other sessions.
4. Migration succeeds/deployment fails: retain additive schema22; never blindly
   downgrade or roll back to an instance with unverified old environment binding.
5. Candidate accidentally released: verify SHA before build and after READY;
   reject latest-branch/local-directory deployment and automatic head migration.

### Task 1: Preflight and fresh recovery — AFTER approval

- [ ] Agree a low-traffic repair window and one migration owner. No other deploy,
  migration, account administration or intentional test writes during the window.
  There is no verified global maintenance switch in this plan: never promise
  zero public writes. If strict write quiescence is required, stop until an
  approved mechanism exists. Capture-to-migration writes require reconciliation
  if recovery is later needed; the owner must accept this residual recovery gap.
- [ ] Recheck exact SHA, clean pinned source, production branch/compute identity,
  current_database=neondb, starting revision18, legacy phone constraint, missing
  auth_version/new tables, aggregate baseline and zero phone conflicts. Changed
  starting state stops execution; do not improvise.
- [ ] Check proposed recovery name unused; stop on collision rather than reuse it.
- [ ] Create a NORMAL current-HEAD branch with create_branch: project as above,
  parent_id=br-polished-surf-axulzu38, name=pre-repair-22-20261015,
  compute min_cu=max_cu=0.25. Do not set an unsupported suspend interval.
  This copies existing data and may incur Neon branch/storage/compute charges.
- [ ] Verify returned branch parent, copy LSN/timestamp, separate endpoint,
  readability of neondb/revision18 and aggregate equality. Record lifecycle;
  no automatic expiration/deletion is requested. Retain both recovery copies.
  If creation/verification fails, STOP before production SQL.

### Task 2: Bounded production transaction — AFTER Task1 passes

- [ ] Use the SAME execution path as the recorded rehearsal: pinned repository
  Alembic-generated SQL via Neon run_sql_transaction, explicitly supplying
  project, production branch, production compute and database IDs above.
  No connection-string retrieval is necessary. This is NOT an online
  psycopg/Alembic CLI verification.
- [ ] Regenerate command.upgrade(config,'20260909_18:20261014_22',sql=True), compare
  with the retained artifact, and preserve statement boundaries (in particular
  DO dollar-quoted blocks; NEVER split indiscriminately on semicolons). Use only
  emitted DDL/data/version statements, with MCP providing the transaction.
- [ ] Before emitted statements in that transaction: SET LOCAL lock_timeout='5s',
  SET LOCAL statement_timeout='60s'; acquire the agreed transaction advisory
  migration-owner lock and assert database/revision/preconditions. Capture start
  and finish times without logging SQL parameters or personal values.
- [ ] Commit ONCE. On error, STOP: independently inspect revision/rollback and
  sanitized SQLSTATE. Do not replay, extend limits or kill blockers automatically.
- [ ] Independently verify exactly22, auth_version NOT NULL/default0, Terms and
  vehicle-document tables, verified-phone check/index, removed legacy constraint
  and preservation aggregates. Record timing. If postconditions fail, do not deploy.

The old generic GitHub migration workflow uses upgrade head. DO NOT dispatch it
for this repair. An online operator alternative would require a separately
reviewed masked direct URL and bounded command, not a silent execution-path swap.

### Task 3: Same-SHA API redeployment — AFTER Task2 passes

- [ ] Redeploy API only, using the existing deployment as source with latest
  Production project settings. Verify the redeploy operation consumes current
  settings rather than replaying old environment/build artifacts; if unavailable
  through the connector, stop for the owner to use Vercel's Redeploy operation.
- [ ] Pin SHA ccd594df8a78f56041876c058b522e0624db4fb6 explicitly; do not select
  latest main or upload the dirty local checkout. Target production, API project
  and team above. No frontend deployment, secret rotation or environment edits.
- [ ] Wait for READY, confirm new deployment ID, same SHA and API alias assignment.
  A successful build is not the acceptance check. Inspect sanitized runtime logs.

### Task 4: Controlled verification and stop conditions

- [ ] Read-only health/live, ready and OpenAPI on the NEW deployment and alias.
  Readiness must show required dependencies available; retain request IDs only.
- [ ] Owner performs ONE login on www.transivox.in using their existing designated
  account; credentials stay in the browser. Approval includes expected writes to
  login timestamp/counters and refresh-session/audit records. Do not create an
  account, issue deliberate bad-password attempts or repeat on failure.
- [ ] Confirm request goes to intended production API, authenticated user/role,
  correct role destination, refresh within the existing deployed design, logout,
  cleared browser credentials, refusal of unauthenticated protected requests and
  rejection of the revoked refresh credential. Do not assume a previously issued
  access JWT is invalidated before its expiry unless this deployed code enforces
  that. Inspect status/request IDs and
  sanitized exception class/SQLSTATE only. No OTP/SMS/payment/document actions.
- [ ] If login fails, capture one sanitized response/log and STOP retries.
  Do not call new cookie-session routes absent from ccd594d or claim browser-close
  persistence/shared acceptance is deployed. Those remain candidate test gates.
- [ ] Report saved owner-confirmed configuration separately from deployment
  provenance, actual login evidence and remaining independent runtime-binding
  limitations. Do not claim host proof solely from READY/health/login.

## Recovery decisions

- Before transaction commit: a failed PostgreSQL transaction should roll back;
  confirm revision/schema independently, retain old deployment and stop.
- After migration but before successful redeploy: keep schema22, investigate build
  or configuration; old deployment's database binding remains unverified. Avoid
  rollback to stale environment settings as an automatic remedy.
- After commit with data recovery needed: stop writes using an approved mechanism;
  obtain separate approval to create a NEW branch from the fresh recovery copy,
  reconcile writes after its copy point and perform a reviewed cutover. Never
  reset production or overwrite either retained branch. No data-loss-free or
  independently restored-backup claim is warranted.

## Requested approval scope

Approve (1) the small fresh normal recovery branch and possible charges,
(2) the single bounded production18→22 migration transaction, (3) API-only
same-ccd594d redeployment using saved current Production settings and (4) one
owner-operated login/role/logout check with its expected session writes, during
the agreed quiet window. Approval is conditional on every preceding gate passing;
unanticipated state/cost/failure stops execution. No commits, pushes, candidate
release, Preview writes or other integrations are included.
