# Release candidate verification — 15 October 2026

This is a local verification handoff, not authorization to push, deploy or migrate
production. Preserve the current uncommitted source and independent S3 probe.

## Secure local PostgreSQL setup

Reuse the approved LOCAL `transivox_e2e` database if it already exists. Never use
Neon, a production database, a normal development database or a superuser URL.
Otherwise use the dedicated Docker procedure in
[the existing handoff](2026-10-14-release-handoff.md#windows-postgresql-setup).
That procedure binds port 55432 to loopback, creates `transivox_e2e_user` with no
superuser/create-role/create-database permissions, and gives it ownership only of
the isolated database. Its PUBLIC connect revocations are for that new dedicated
container only, never a shared PostgreSQL server. Password entry uses `\password`.

In Windows PowerShell, configure the process privately:

```powershell
cd 'C:\Users\harsh\OneDrive\Desktop\english learning\logistic\trucksetu'
$env:APP_ENV='test'
$env:TRANSIVOX_E2E='true'
$env:E2E_REAL_AWS='false'
$env:E2E_ALLOWED_DATABASE_HOSTS='127.0.0.1'
$env:PYTHONPATH='backend'
$env:E2E_PYTHON=(Resolve-Path '.\.venv\Scripts\python.exe').Path
$env:E2E_CONTROL_TOKEN='local-regression-control-only'
$env:SECRET_KEY='local-test-only-never-production-012345678901234567890123456789'
$taskDbSecret=Read-Host 'Restricted LOCAL transivox_e2e URL (password URL-encoded)' -AsSecureString
$env:E2E_DATABASE_URL=[Net.NetworkCredential]::new('', $taskDbSecret).Password
$taskDbSecret=$null
& $env:E2E_PYTHON -m e2e_database validate
if($LASTEXITCODE -ne 0){throw 'Unsafe or missing test database configuration; stop.'}
```

Expected private URL structure is
`postgresql://transivox_e2e_user:<encoded-password>@127.0.0.1:55432/transivox_e2e`.
Do not echo the value, paste it into chat, store it in a committed file, use
`setx`, or put it in a command-line argument. For an existing approved local server,
use its actual port. Validation requires the exact name and allowed local host;
connection-option target overrides and real-AWS reset mode remain prohibited.

## Launch an agent process with the environment

Setting `$env:` in a separate terminal does NOT change an already-running desktop
app or this existing agent process. Launch the installed CLI from the SAME
PowerShell session after the preceding configuration:

```powershell
codex --cd (Get-Location).Path
```

Then ask it to resume this checklist, first check only whether E2E_DATABASE_URL is
set (never print it), validate with e2e_database, and run the guarded regressions.
The installed CLI's `--help` confirms `--cd`; official reference:
https://learn.chatgpt.com/docs/cli/reference . If local agent shell filtering removes
the variable, stop and run the tests directly from this configured PowerShell;
do not weaken filters broadly or fall back to DATABASE_URL.

## Exact isolated migration and test commands

After safety validation succeeds, in that same PowerShell session:

```powershell
# Deliberately bind BOTH application and migration settings to the validated test URL.
$env:DATABASE_URL=$env:E2E_DATABASE_URL
$env:MIGRATION_DATABASE_URL=$env:E2E_DATABASE_URL
Push-Location backend
try {
  & $env:E2E_PYTHON -m alembic -c alembic.ini upgrade head
  if($LASTEXITCODE -ne 0){throw 'LOCAL migration failed; stop.'}
  & $env:E2E_PYTHON -m alembic -c alembic.ini current
  if($LASTEXITCODE -ne 0){throw 'Cannot verify LOCAL migration revision.'}
} finally { Pop-Location }
& $env:E2E_PYTHON -m pytest backend/tests/integration -q -p no:cacheprovider
if($LASTEXITCODE -ne 0){throw 'Database regression failed; inspect sanitized output.'}
npm run e2e
if($LASTEXITCODE -ne 0){throw 'Local KYC journey failed.'}
npx playwright show-report
```

Expected head: `20261014_24`. The release schema regressions additionally run the
REAL migration functions from base through 23 and 24 in unique generated schemas
inside that exact database, seed fictional records before23, verify preservation,
then drop ONLY their own generated schemas. No `create_all`, production migration,
database fallback, broad reset or real AWS is involved. Ordinary KYC `npm run e2e`
does reset the guarded LOCAL test database; do not run it during another test run.
Do not run browser suites concurrently: they share ports/artifact directories.

Legacy `test_pilot_auth_database.py` is separately opt-in. Its old `_test` database
convention was removed: it now requires safe_database_url and refuses an API
configuration not bound to that exact isolated URL. Main CI now provisions the
same restricted transivox_e2e role/database and runs all integration regressions;
the local command leaves that one redundant legacy smoke opt-in disabled unless
you set PILOT_E2E_DATABASE=1. GitHub workflow execution remains unverified here.

## Migration23 effects and release caution

- Adds nullable KYC object VersionId; never guesses a version for old evidence.
- Every previously verified provider becomes `resubmit_required` with an audit
  entry. Verified applications require resubmission and old unbound document rows
  become rejected; files and prior history remain.
- It does NOT delete or reassign bookings/trips/vehicles/drivers, change booking
  prices, or directly change DriverProfile flags. Existing trip updates continue
  to use their existing assigned-party rules; NEW quotes/routes/holds/bookings
  and assignments enforce authoritative provider/driver identity eligibility.
- A linked driver's old verified flag does not substitute for its identity KYC.
- With no real scanner, re-verification cannot finish; this can block new business
  operations. Production provider/booking/assignment counts and impact have NOT
  been inspected. Owner approval of the policy is not a production migration run.
- Migration24 adds route-bound quote/request references, quote breakdown/expiry,
  version snapshot and unique acceptance key. Existing values are preserved.

## Proposed commit contents — not staged or committed

1. `feat: add explicit shared quote acceptance and secure browser sessions`:
   current API/model/schema/migration24 changes; shared request/quote/revision/
   acceptance/operator UI; auth client/startup changes and their tests; configuration,
   version reporting, migration checker and documentation. Requires the guarded
   DB release gates before treating this as a validated deployable candidate.
2. `test: verify shared capacity races and release migration effects`:
   guarded PostgreSQL helper/scenarios plus cookie/financial/KYC regressions,
   browser tests, and final release evidence. Keep tightly coupled assertions with
   the production change if splitting would leave a commit untested.
3. Independent optional S3-probe work stays separately reviewed, not silently
   bundled. Never include generated `src/transivox_api.egg-info/`, `.superpowers/`
   scratch data, `.env*` secrets, reports, traces, sample IDs or credentials.

Diff review must include UNTRACKED source/tests, not just `git diff`, and compare
against HEAD d5f4306 plus the already-pushed release baseline versus origin/main.
No new release commit SHA exists until separately authorized commit creation.

## Evidence

Current run counts and independent review findings are recorded in the existing
[release checklist](2026-10-14-release-candidate-checklist.md). Database execution
is blocked while E2E_DATABASE_URL is absent. Collection is not a passing test.

Latest executed checks: 324 backend nonintegration,46 frontend,37 built-preview
browser checks passed; the three shared workflow browser checks additionally
passed after 390px overflow assertions were added to the operator/provider forms.
Build/lint/domain typing/offline migrations/whitespace passed. 26 DB tests only
collected. Initial dev-server run failed36/37 due cold transformations; built-
preview run passed without raising timeouts. Independent final reviewer hit a
usage limit; self-review only, not independent release approval. Real AWS scanner
configuration/scan success and full deployed KYC approval remain blocked.

### Database-only continuation — 15 October 2026

- Inherited `E2E_DATABASE_URL` was present; its value was not printed.
- Repository `e2e_database validate` passed with explicit test mode, real AWS
  disabled, and loopback-only allowed hosts. The configured local port is 5432;
  its TCP listener is reachable and the local PostgreSQL 16 service is running.
- A read-only connection attempt was rejected by PostgreSQL password
  authentication. No database identity, restricted-role flags or current Alembic
  revision could therefore be verified. URL validation alone is not role proof.
- Database regressions: 0 executed, 0 passed, 0 failed, 0 pytest skips; all 26
  previously collected cases remain blocked before execution. Database-backed
  multi-role journeys were not started. Completed non-database suites were not
  repeated.
- Migrations 23/24 were not applied or verified. No reset, fake scanner, database
  mutation, production access, commit, push or deployment occurred.
- Next action: correct the restricted local role credentials privately using the
  approved local setup, set the URL in the same PowerShell session, and relaunch
  the agent from that session. Then repeat safety/role/revision preflight before
  isolated migrations, the 26 PostgreSQL regressions and database-backed journeys.
