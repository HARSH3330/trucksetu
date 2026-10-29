# Coordinated release preparation — 27 October 2026 IST

> **29 October update:** approved read-only reconciliation is complete and the new endpoint is confirmed suspended. Retained-state reconciliation PASS; historical zero-write/no-loss guarantee remains limited by missing history. No data repair is indicated. See [29 October findings](2026-10-29-incident-reconciliation.md) and [sanitized evidence](2026-10-29-incident-reconciliation-evidence.json). Earlier observations below retain their original dates. Production execution remains BLOCKED.

Decision: **NO-GO for production execution.** Local artifacts and the proposed sequence are concrete; recovery closure, backup readiness and a final reviewed source commit/hosted CI are not. This report authorizes no deployment, production migration, data repair, endpoint movement, configuration change or email.

## Source and preservation

Repository: `C:\Users\harsh\OneDrive\Desktop\english learning\logistic\trucksetu`. Read `AGENTS.md`, `docs/PROJECT_HANDOFF.md`, the reviewed coordinated release plan and recovery incident plan before investigation. Branch and HEAD match the handoff: `release/customer-first-20261026`, `fa2595741d261cf15d2c0849b13e446d1eaffd20`. Initially only the handoff was modified; its existing contents were preserved.

An isolated Git archive of that exact commit was extracted under `C:\Users\harsh\OneDrive\Documents\ChatGPT\truck\release-prep-fa259574\source`. No production credentials or repository `.env.local` files were copied into that source export. Public browser Maps values were read privately from the frontend project's Production entries and used in the frontend build; their literal values are omitted from evidence. Browser keys are necessarily embedded in the distributable frontend assets. No server secrets were pulled.

Four correction paths remain uncommitted:

- `e2e/fixtures/customerJourney.ts`: use a prefix label lookup for the customer PAN decision. Real component reproduction found zero exact-label matches and one prefix-label match because the wrapping label also contains option text. The original helper fails at this selector in hosted CI; the patched helper successfully submits a mocked local review through the actual component. Subsequent real local desktop/mobile customer-review journeys passed; the old hosted CI job remains failed until a new exact-head run.
- `.github/workflows/playwright.yml`: build `vite.maps-harness.config.ts` before the simulated Maps suite. Its static server requires `.tmp/maps-browser-dist`, which was absent in a fresh source export. The build generated it and all five simulated browser checks passed.

- `src/components/DemandWorkspace.tsx`: closing the bid editor with Escape did not restore focus to its launch button. The existing real browser assertion failed; added cleanup to restore the connected prior focused element. The provider action labelled Active trips & bookings also pointed to the read-only booking summary rather than the existing trip-operations view; it now uses trips. Both runtime defects were reproduced by the existing browser journey. These ARE frontend runtime changes; backend payment and trip-authorization rules are unchanged.
- `e2e/release-demand-management.spec.ts`: implicit select labels and prefilled textarea labels contain option/initial-value text, so exact whole-label lookups failed. Use unambiguous prefix/partial matching without weakening business assertions. Target the actual trip-operations route, wait for confirmed assignment before navigation, and reload after API-only fixture creation when the hash is unchanged. The final targeted management journey passed; failures were not bypassed or converted into skipped checks.

HEAD has not changed. No commit or push was authorized or performed. Original base artifacts remain preserved. Corrected frontend/source artifacts have explicit base-commit-plus-patch provenance; they are NOT a new immutable Git commit and are not approved for deployment. A future reviewed commit and exact-head hosted CI are required before production approval.

## Recovery investigation: read-only findings and limits

Project: `morning-forest-29164100`; database: `neondb`. SQL used explicit `REPEATABLE READ, READ ONLY` transactions and a 15-second statement timeout. No production application row, schema or endpoint was changed. The sanitized comparison SQL is retained locally as `incident-compare-readonly.sql`.

| Object | Current observation | Status |
|---|---|---|
| Original database | `br-polished-surf-axulzu38`, name production, primary/default true, protected false; original endpoint `ep-fragrant-surf-axkjz078` bound here | PASS for identity; protection BLOCKED |
| Original schema | Read-only query returned `20261014_22` | PASS |
| Incident recovery copy | `br-young-wind-axoimpov`, name recovery-rehearsal-20261026-not-preview, restore finalized from `snap-little-tree-ax4fn88h`, not primary/default, protected false | PASS for preservation/identity; rows BLOCKED |
| Recovery-copy access | Resolved 29 October: one authorized 0.25-CU read_only endpoint ep-morning-sunset-axii59da verified, used for read-only comparisons and suspended. Fresh schema29 confirmed; detailed results in 29 October addendum | PASS for scoped access; historical closure still limited |
| Holding copy | `br-misty-recipe-ax4djqgq`, parent original at `2026-10-26T02:35:24Z`, endpoint `ep-wandering-credit-axfl5bss`; read-only query returned 22 | PASS |
| Snapshot | `snap-little-tree-ax4fn88h`, pre-release-20261026-do-not-delete, source original, created `2026-10-26T02:17:08Z` | PASS for retained metadata; not a verified fresh release recovery point |
| Older copies | pre-migration-20261015 (`br-morning-base-ax0dr2z2`), migration-rehearsal-20261015 (`br-weathered-hill-axdizmg3`), pre-repair-22-20261015 (`br-frosty-mountain-ax2vpqat`) remain listed | PASS for retained metadata; not substituted for incident-copy inspection |

Incident window from the incident plan: **26 October 2026, 07:47:21–08:06:15 IST** (`02:17:21–02:36:15 UTC`). Provider operation history corroborates original endpoint activity on the recovery branch at 02:17:56 and 02:29:42 UTC, replacement endpoint activity on the original branch at 02:31:37, holding-branch creation at 02:35:49, and original endpoint activity back on the original branch at 02:36:13. These operations establish infrastructure activity, not which business requests committed.

Across **49 application tables**, original and holding had equal row counts and equal order-independent full-row fingerprints. Fingerprints and raw records are not printed or persisted in this report. Nonempty tables: users 6, user_roles 6, account_verifications 5, refresh_sessions 26, audit_logs 3, application_settings 1, trip_price_estimates 3. Other compared tables were empty. No rows had an observed creation/update/action timestamp in the incident window in either queried copy. This covers current retained records with those timestamp columns; it cannot detect deleted records or guarantee coverage of changes without timestamps.

The holding copy descends from the original near the end of the incident. Equality with it is NOT a comparison against the database that served the original endpoint during the incident. It therefore does not establish that writes were not left on the recovery branch, lost or duplicated.

Both original and recovery branch `pg_endpoint` log queries returned empty arrays for the bounded incident window. The Vercel backend runtime-log request explicitly failed because the incident window exceeded Hobby retention. Empty logs are not evidence of zero traffic. No archived request logs, database audit stream or WAL history establishing all incident writes was available. The production runtime's private database connection binding also remains unavailable through sensitive environment metadata.

**29 October: retained-state reconciliation PASS.** Approved access and three-way comparison are complete: 49 common tables covered with no truncation or omitted original columns; recovery matches holding, seven recovery-only tables are empty, and the only original differences are two sessions and one last-login field proven after the incident. No surviving recovery-only records or incident-related duplication/data loss were detected. A historical zero-write/no-loss guarantee remains BLOCKED by absent request/audit/WAL history; owner review of that residual uncertainty is needed for closure. No repair is indicated. Preserve every copy and snapshot; the new read-only endpoint is suspended. See the linked 29 October report for exact scope and limitations.

## Production configuration verification

Environment inspection occurred on 26 October; deployments were rechecked on 27 October. No settings were changed.

| Item | Evidence | Result |
|---|---|---|
| Frontend project | trucksetu-whri / `prj_3TQcT6qyOPBQlAguSubP2OJ5xe7w`, team `team_iu09mmhsbf90RQTBtkgvOHlX` | PASS |
| VITE_GOOGLE_MAPS_BROWSER_KEY | Present, Production-only, nonempty and expected key shape; literal value omitted | PASS for configuration shape only |
| VITE_GOOGLE_MAPS_MAP_ID | Present, Production-only, nonempty, not DEMO_MAP_ID; literal value omitted | PASS for configuration shape only |
| Frontend VITE_API_URL | Entry is sensitive, so stored value could not be compared. Local production-target build explicitly used the reviewed backend alias plus /api/v1 | BLOCKED for stored-value correctness |
| Google Cloud acceptance | No independent proof of project ownership, Map ID type, billing, Maps JavaScript API/Places API (New) enablement or exact `https://www.transivox.in/*` restrictions | BLOCKED |
| Backend project | trucksetu-api / `prj_gXnKmzBiPf8TpQ5MJmZLQPg04diF` | PASS |
| SMTP_HOST / SMTP_PORT / SMTP_USERNAME / SMTP_PASSWORD / EMAIL_FROM | All exist as sensitive Production-only variables. Values are unavailable, so correctness/population/matching cannot be asserted | PASS for presence; correctness BLOCKED |
| Required SMTP behavior from candidate | `communications.py` uses SMTP with certificate-verified STARTTLS and SMTP login. Required Brevo inputs are host smtp-relay.brevo.com, port 587 for this reviewed flow, actual Brevo SMTP Login and an SMTP key. It does not use a Brevo API key or implicit SSL on port 465 | Private value confirmation BLOCKED |
| EMAIL_REPLY_TO | Supported but optional; absent entry is not a failure | PASS for optionality |
| PUBLIC_FRONTEND_URL | Exact readable Production value matches https://www.transivox.in | PASS |
| Sender | Brevo sender API confirms the intended noreply@transivox.in sender active; hidden backend EMAIL_FROM value cannot be compared | PASS for sender activation; exact deployed sender match BLOCKED |
| Mail delivery/receipt/authentication | Prior local SMTP and owner-provided mailbox evidence reused as historical local evidence only; no production send in this task | BLOCKED for production |

Private locations: frontend and backend project Settings -> Environment Variables in Vercel; Brevo Settings -> SMTP & API -> SMTP for login/key, and Senders/Domains for sender authentication; Google Cloud Credentials and Maps Management for API/referrer restrictions and Map ID ownership. Preserve Local and Preview credentials. Do not put server secrets in VITE variables. Duplicated backend SMTP variable names remain in the frontend project; they were neither used nor removed by this work.

## Serving source and why redeploying selected old main

Fresh alias lookups show:

- www.transivox.in: `dpl_APPh8etW4m7yRoC4zDSyjtkWeExi`, READY Production.
- trucksetu-api-nine.vercel.app: `dpl_7pdmUXDmaY9bjQZFRxbPX8n3wyGe`, READY Production.
- Both report `source=redeploy`, Git ref main, SHA `ccd594df8a78f56041876c058b522e0624db4fb6`.

Redeploy reused the selected old deployment's source. Changing environment values does not change that source reference. Both candidate Vercel root configs intentionally disable automatic Git deployment for release/customer-first-20261026. No release branch deployment or promotion was performed. Do not enable auto-deployment as a shortcut or merge an incompatible API onto revision 22.

## Local verification and artifacts

| Check | Result | Evidence |
|---|---|---|
| Backend unit suite | PASS | 430 passed, 3 warnings; production network/SMTP disabled and database URL pointed to unused loopback port; first temporary-directory/test-flag failures corrected in runner environment |
| Frontend unit suite | PASS | 54 tests / 13 files |
| Backend Ruff and domain mypy | PASS | All checks passed; no issues in 1 source file |
| Offline migrations | PASS | One head 20261025_29; clean PostgreSQL upgrade SQL compiles without a database connection |
| Frontend candidate build | PASS | Node 24.13.0, locked npm install; reviewed public API origin and actual frontend Production Maps values; known nonfatal bundle-size warning |
| Backend artifact build | PASS | Python 3.12.14 wheel produced; installed dependency versions retained locally in python-installed-packages.json |
| Focused review helper | PASS, mocked local API | Exact selector reproduced as zero matches; patched actual helper submitted accepted document review through real component |
| Maps browser simulations | PASS, simulated Google/API boundaries | 5 passed, includes mobile/desktop, failure/manual fallback and stale Places results |
| Email browser simulations | PASS, simulated account API | 2 passed, desktop/mobile, explicit submission and fragment removal; no real email |
| Candidate hosted CI | Backend/frontend/containers PASS; browser FAIL | Exact head fa259574, browser job 121596829384/run 40330071570: 8 legacy/session/shared/vehicle checks passed, three customer-review cases failed; later dedicated suites skipped. Local corrections are not a rerun of that job |
| Fresh isolated migration regressions | PASS | Started installed Docker Desktop normally and ONLY the preserved transivox-e2e-postgres container (postgres:16-alpine, existing transivox_e2e_postgres_data volume, 127.0.0.1:55432). Verified exact database/role and no superuser/create-db/create-role/replication privileges. Four real migration regressions passed in disposable synthetic schemas, including historical fixtures at the 22/23 boundary, customer KYC and private locations. No production/incident copy used |
| Database-backed customer review browsers | PASS | Both desktop/mobile customer consent/scan/review journeys passed after the label fix. Existing local rows were preserved; setup explicitly forbids resets |
| Database-backed demand management | PASS | Final targeted local run: 1 passed (local-management-final.log). Exercises bid revision/withdrawal, signed SIMULATED captured-payment event handling/idempotency, assignment, trip authorization/OTP gates, cancellation and persisted refund-request history. No actual provider payment/refund call; this is not real 99-INR payment/refund acceptance |
| Old-code/new-schema rollback compatibility | BLOCKED | No claim that the old production API is safe to roll back onto schema 29; automatic old API rollback remains prohibited |

Artifacts at `C:\Users\harsh\OneDrive\Documents\ChatGPT\truck\release-prep-fa259574`:

| File | SHA-256 |
|---|---|
| candidate-source.zip | 9406c634cbf3719e952e30f3523979d8e12aa94559b3fcdacb9b8c3a9b45bf67 |
| artifacts/frontend-fa259574.zip | e75416596bc94ff792c07f0405c46cc4b05bdbc718929cb69162771799b34a33 |
| artifacts/backend-source-fa259574.zip | 9c3cd5438efdfecbf86a3b497d542a34f328b5a2a0fcfee482c4ca6c53e462f3 |
| artifacts/transivox_backend-1.0.0-py3-none-any.whl | 74501b3148257430cd9561be6957949c675bbc4e3587e7c9c689be4e50b8dca2 |


Corrected local candidate provenance: base `fa2595741d261cf15d2c0849b13e446d1eaffd20`, uncommitted patch SHA-256 `f070e9d32a4740cbcfd0cdbd5bb8921be1133f967e57e16d5cf9f69b81976440`; final Git commit: **BLOCKED/not created**.

| Corrected artifact | SHA-256 |
|---|---|
| artifacts/candidate-fa259574-plus-local-fixes.zip | 369fceeababdf09e840e795ea34d80b4a629ed0ca105c9963bba399d06e87fd3 |
| artifacts/frontend-fa259574-plus-local-fixes.zip | 6c28ee7000b8809b64d2c560196f8aa7995000a6aa3ceb49908c6027bcff303d |
| release-local-fixes.patch | f070e9d32a4740cbcfd0cdbd5bb8921be1133f967e57e16d5cf9f69b81976440 |

`artifact-manifest.json` is authoritative for hashes, source identity and limitations; its repository copy is docs/operations/2026-10-27-coordinated-release-artifacts.json. These are LOCAL build/source artifacts, not `.vercel/output` packages or staged Vercel deployment IDs. Backend wheel contains application code; backend-source ZIP also includes migrations, Alembic config and deployment source. Vercel runtime/build/config attestation and server-secret correctness remain blocked. Python dependency declarations are ranges; the local installed-package inventory is evidence, not an approved cross-platform dependency lock.

Rerun commands from the local isolated source (with the same safe test-only environment as the retained logs): `npm test`; `npm run build`; `..\.venv\Scripts\python.exe -m pytest backend/tests --ignore=backend/tests/integration -q -p no:cacheprovider --basetemp=..\pytest-unit-temp`; `scripts\check-migrations.ps1 -Python <absolute isolated Python path>`. The focused component/helper reproduction is `node reproduce-review.mjs`. The Maps and email suites used separately managed loopback servers plus the local `playwright.maps-local.config.ts` and `playwright.email-local.config.ts`; their APIs were mocked. Rehearsal rerun from the prep directory: `./run-local-rehearsal.ps1 -Mode migrations`; customer journeys: `./run-local-rehearsal.ps1 -Mode journeys`; management only: `./run-local-rehearsal.ps1 -Mode management`. The runner reads an existing private local DPAPI credential without printing it and validates loopback/database/role before tests. Do not copy its credential to production or Preview. Do not run these commands against production or treat the exported source as an approved new Git commit.

## Reviewed migration and release sequence — proposal only

Current observed production revision: `20261014_22`; target: `20261025_29`. Inspected migration files 23–29 and migration environment in the candidate:

1. 23 adds KYC storage-version pins, audits/requires re-verification and rejects legacy unbound documents; it changes business eligibility.
2. 24 adds shared route references, quote expiry/breakdowns/version snapshots and unique booking acceptance key.
3. 25 adds legacy-preserving marketplace mode/revision, drafts/selections and an independent connection-fee ledger.
4. 26 adds private customer KYC history/active-document constraints.
5. 27 backfills contact-reveal history from existing audit and records refund obligations/credits.
6. 28 adds durable refund execution/reconciliation metadata, without initiating refunds.
7. 29 adds nullable private location columns; the new API selects these, so deploying it on 22 is incompatible.

All seven downgrades explicitly refuse destructive rollback. The Alembic environment wraps upgrades in a transaction. Fresh local regression tests exercised real migration operations through 29 with historical fixtures inserted before 23 and proved current API behavior on the resulting schema. These tests do not prove the old API/new-schema rollback pair or a fresh production backup restore. Those acceptance gaps remain release/rollback gates. Offline SQL compilation alone would not satisfy migration validation. No production migration occurred here.

Proposed limited release keeps real and sandbox checkout false, tax confirmation false, KYC/scanning fail-closed and all unapproved operational capabilities disabled. It does not authorize a fully operational paid launch. Existing scanner/consent/privacy/tax/99-INR payment/refund gates from the reviewed plan remain open and are not investigated afresh here.

Order after all gates and explicit approval:

1. Close incident evidence gaps; confirm private runtime-to-production DB binding. Review/commit local test fixes, obtain green exact-head CI and freeze the final source/config/dependency manifest. Do not ship a dirty tree or silently substitute a future SHA.
2. Confirm project roots and private settings, cross-site auth cookies/CORS/trusted hosts, production URL, payment gates and disabled test/bootstrap controls. Verify Google ownership/restrictions/Map ID and privately confirm matching Brevo SMTP/sender values. Build immutable target-platform frontend/API deployment artifacts from that same final SHA; approve their exact digests. No deployment build can be represented as fully attested from a local wheel alone.
3. Approve a maintenance window/operator, measured RPO/RTO, fresh protected recovery point and encrypted backup location; test restore into a separately approved isolated destination. Existing snapshot/copies are preserved but unprotected and insufficient as a fresh verified release recovery plan. No protection/paid-plan/backup resource change was authorized here.
4. Hold incompatible public writes with the reviewed maintenance control, preserve signed webhook retention/retry handling, and recheck actual aliases/bindings/revision/current financial work. With the approved direct migration identity and exact source: inspect current (must be 22), run `python -m alembic -c alembic.ini upgrade 20261025_29` from backend ONCE, verify current/head 29. Do not dispatch floating `upgrade head`, stamp or retry blindly.
5. Deploy/stage the approved API to trucksetu-api without assigning public aliases where supported. Validate approved staged access, then promote API while traffic remains held. Check liveness/readiness/version/DB compatibility. Stop on any failure; do not publish frontend over an incompatible API.
6. Stage/promote frontend from the SAME approved SHA and reviewed public build configuration to trucksetu-whri. Check canonical www, exact API origin and the post-release matrix below. Release traffic only for approved capabilities.
7. Keep incident evidence and financial/audit/version history. Prefer forward fix. A frontend rollback requires compatible API/schema; old API rollback after 29 is not approved by additive columns alone because of KYC/contact/security behavior. No destructive downgrade or automatic database restore. Any restore/cutover requires its own measured-data-loss/replay approval.

No production approval can be fully specified yet: final corrected source SHA, green browser CI, target Vercel deployment outputs/digests, verified production binding, incident closure, fresh protected backup/restore proof, maintenance window/operator and RPO/RTO are missing. These are explicit prerequisites, not permission to bypass them.

## Post-release acceptance plan — not performed

- Confirm both serving aliases identify the exact approved source SHA/deployment IDs; inspect `/version`, `/health/live`, `/health/ready` and schema revision through approved read-only access. Verify test/reset/bootstrap controls are unavailable. READY metadata is insufficient.
- On https://www.transivox.in, load Google map and Places New autocomplete, select/adjust a real place/pin, confirm address/attribution and failure/manual fallback. Check browser restrictions and real provider errors privately. Do not publish demands, send arbitrary data to Google, or incur unauthorized provider usage. Real production Google calls require acceptance scope in release approval.
- Email source-confirmed routes: POST `/api/v1/auth/signup`, POST `/api/v1/auth/verify-email`, POST `/api/v1/auth/verification/resend`, POST `/api/v1/auth/password-reset/request`, POST `/api/v1/auth/password-reset/confirm`; session checks use existing `/api/v1/auth/me` and `/api/v1/auth/session/refresh`. Inspect request schemas at the frozen final SHA before use.
- Existing recipient authorization is PASSWORD RESET ONLY. Confirm the supplied address is a dedicated test account before any request/reset; do not reset an existing customer. Verification/resend/signup need separate recipient authorization. Set an explicit request/send budget before testing (no polling/retry loops). Current proposed reset-only budget is one reset request and at most one reset email, one confirm, one reuse rejection, two old-session checks and one new-password login. Stop on unexpected status or missing evidence.
- Keep passwords, access/refresh credentials, codes/tokens and message links in memory/hidden local prompts only. Check exact frontend link origin https://www.transivox.in before use. Do not print/store full links or use direct SMTP as an application substitute.
- Report API acceptance, provider delivery evidence, owner-confirmed mailbox receipt/Inbox-or-Spam, SPF/DKIM/DMARC and actual working production link separately. The owner must confirm receipt privately; request no message bodies, tokens or full links in chat. Unavailable evidence stays BLOCKED. Verification cooldown/reuse checks and session invalidation require explicit authorized test scope; they have not been performed in production.

## Approved reconciliation completed; separate release boundary

The owner approved exactly one independent 0.25-CU read_only endpoint on the preserved recovery copy. This was completed on 29 October: ep-morning-sunset-axii59da, verified recovery binding and physical replica, bounded READ ONLY comparisons, then explicit suspension. Final state idle, suspended_at 2026-10-29T08:51:31Z; all existing endpoint bindings and original primary/default preserved. No resource deletion, data repair, endpoint move, plan upgrade, production migration, deployment or email. The completed approval must not be reused to create another endpoint.

Next: owner review of retained-state PASS and the missing historical-log evidence. Supply archived incident history if a stronger conclusion is required, or explicitly accept documented residual uncertainty for incident closure. No repair request is warranted by the retained data. The 29 October [report](2026-10-29-incident-reconciliation.md) distinguishes this from proving no historical writes ever occurred.

Production execution remains BLOCKED on a final reviewed commit/green exact-head hosted CI, private configuration/binding acceptance and fresh backup/restore readiness with an operator/window/RPO/RTO. A separate production approval must name final SHA, target-platform artifact/deployment identifiers, exact22-to-29 sequence, recovery point and post-release scope. No production release approval is requested by this scoped reconciliation.


Local rerun prerequisite: start ONLY the preserved dedicated container with `docker start transivox-e2e-postgres` before the guarded runner. It was returned to stopped state after verification; its volume and existing rows were preserved. Do not reset the database or substitute a cloud endpoint.

## Approved reconciliation update — 29 October 2026

Retained-state reconciliation PASS; no surviving recovery-only writes detected. Historical zero-write/no-loss assurance remains BLOCKED pending archived evidence or explicit owner acceptance of the documented uncertainty. New endpoint ep-morning-sunset-axii59da is suspended/idle. All prior copies/snapshot and five existing endpoint bindings remain preserved. Artifact integrity was freshly verified; original tests are reused, not rerun. Both production aliases still serve old main ccd594d. Current production22 / candidate29 unchanged. Full evidence and next actions are in the 29 October report.


## Owner sign-off for release preparation — 29 October 2026

The owner explicitly accepted the documented retained-state reconciliation and historical-evidence limitation, and signed off the incident for release preparation. This is NOT a claim of absolute proof of no historical data loss. Preserve all incident copies and snap-little-tree-ax4fn88h. The one approved recovery read-only endpoint remains suspended. No data repair is indicated or authorized.

Incident sign-off removes the incident-owner-review preparation gate. Production execution remains separate: final exact-head CI, private settings confirmation, fresh backup/isolated restore readiness and a reviewed migration/deployment window are still required. No migration, deployment, data repair, plan upgrade or email is authorized by this sign-off.
